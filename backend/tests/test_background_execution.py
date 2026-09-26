from __future__ import annotations

import pytest

from app.ai.errors import (
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.background.commands import (
    AIAnalysisCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue
from app.background.worker import (
    BackgroundExecutionResult,
    BackgroundWorker,
    DuplicateCommandError,
    classify_background_failure,
)


class FakeAIProvider:
    def analyze(self, context):
        return context


class FakeResearchRun:
    def __init__(self, id_value: int):
        self.id = id_value


class FakeSession:
    def __init__(self, mapping: dict[int, FakeResearchRun]):
        self._mapping = mapping
        self.closed = False

    def get(self, research_id: int, _table=None):
        return self._mapping.get(research_id)

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize(
    ("command", "expected_service_name"),
    [
        (CompetitorDiscoveryCommand(research_run_id=10), "competitor_discovery_service"),
        (
            CompetitorResearchCommand(research_run_id=11, competitor_ids=[1, 2]),
            "competitor_research_service",
        ),
        (
            SourceCollectionCommand(
                research_run_id=12,
                competitor_id=3,
                competitor_research_id=7,
                source_id=9,
            ),
            "source_collection_service",
        ),
        (
            AIAnalysisCommand(
                research_run_id=13,
                scope="competitor",
                provider=FakeAIProvider(),
                competitor_research_id=8,
            ),
            "ai_analysis_service",
        ),
    ],
)
def test_background_worker_executes_queue_to_dispatcher_to_service(monkeypatch, command, expected_service_name):
    queue = InMemoryQueue()
    queue.enqueue(command)

    session = FakeSession({
        10: FakeResearchRun(10),
        11: FakeResearchRun(11),
        12: FakeResearchRun(12),
        13: FakeResearchRun(13),
    })

    def fake_get_research_run(db_session, research_id):
        return db_session.get(research_id)

    monkeypatch.setattr("app.background.dispatcher.get_research_run", fake_get_research_run)

    def competitor_discovery_service(db, research_run_id):
        return {"service": "competitor_discovery_service", "research_run_id": research_run_id, "status": "completed"}

    def competitor_research_service(db, research_run, competitor_ids):
        return {"service": "competitor_research_service", "research_run_id": research_run.id, "competitor_ids": competitor_ids, "status": "completed"}

    def source_collection_service(db, research_run, competitor_id, source_id, competitor_research_id=None):
        return {
            "service": "source_collection_service",
            "research_run_id": research_run.id,
            "competitor_id": competitor_id,
            "source_id": source_id,
            "competitor_research_id": competitor_research_id,
            "status": "completed",
        }

    def ai_analysis_service(db, research_run_id, *, provider, scope, competitor_research_id=None, competitor_research_ids=None, contract_version="contract-v1", prompt_version="prompt-v1"):
        return {
            "service": "ai_analysis_service",
            "research_run_id": research_run_id,
            "scope": scope,
            "provider": provider.__class__.__name__,
            "competitor_research_id": competitor_research_id,
            "competitor_research_ids": competitor_research_ids,
            "status": "completed",
        }

    dispatcher = BackgroundDispatcher(
        competitor_discovery_service=competitor_discovery_service,
        competitor_research_service=competitor_research_service,
        source_collection_service=source_collection_service,
        ai_analysis_service=ai_analysis_service,
    )
    worker = BackgroundWorker(queue=queue, dispatcher=dispatcher, db_session_factory=lambda: session)

    result = worker.run_once()

    assert result is not None
    assert result.status == "completed"
    assert result.command == command
    assert result.result["service"] == expected_service_name
    assert session.closed is True


def test_worker_closes_session_when_dispatch_raises():
    queue = InMemoryQueue()
    queue.enqueue(CompetitorDiscoveryCommand(research_run_id=20))

    session = FakeSession({20: FakeResearchRun(20)})

    def boom_service(db, research_run_id):
        raise ValueError("dispatch failed")

    dispatcher = BackgroundDispatcher(competitor_discovery_service=boom_service)
    worker = BackgroundWorker(queue=queue, dispatcher=dispatcher, db_session_factory=lambda: session)

    result = worker.run_once()

    assert result is not None
    assert result.status == "failed"
    assert isinstance(result.result, ValueError)
    assert session.closed is True


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: CompetitorDiscoveryCommand(research_run_id=0), "research_run_id must be a positive integer"),
        (lambda: CompetitorResearchCommand(research_run_id=1, competitor_ids=[]), "competitor_ids must not be empty"),
        (lambda: AIAnalysisCommand(research_run_id=1, scope="competitor", provider=FakeAIProvider()), "competitor_research_id is required for competitor scope"),
        (lambda: AIAnalysisCommand(research_run_id=1, scope="research_run", provider=FakeAIProvider(), competitor_research_ids=[]), "competitor_research_ids is required for research_run scope"),
    ],
)
def test_background_commands_validate_basic_contract(factory, message):
    with pytest.raises(ValueError, match=message):
        factory()


def test_background_worker_retries_retryable_failures_and_avoids_duplicates():
    queue = InMemoryQueue()
    command = CompetitorDiscoveryCommand(research_run_id=21, max_attempts=3)
    queue.enqueue(command)

    def flaky_service(db, research_run_id):
        raise TimeoutError("temporary outage")

    dispatcher = BackgroundDispatcher(competitor_discovery_service=flaky_service)
    worker = BackgroundWorker(queue=queue, dispatcher=dispatcher, db_session_factory=lambda: object())

    result = worker.run_once()
    assert result is not None and result.status == "retry_scheduled"
    assert result.retryable is True
    assert result.attempt_count == 1
    assert len(queue) == 1
    assert queue._items[0].attempt_count == 2

    result2 = worker.run_once()
    assert result2 is not None and result2.status == "retry_scheduled"
    assert result2.retryable is True
    assert result2.attempt_count == 2
    assert queue._items[0].attempt_count == 3

    result3 = worker.run_once()
    assert result3 is not None and result3.status == "failed"
    assert result3.attempt_count == 3
    assert len(queue) == 0

    queue.enqueue(command)
    terminal_duplicate = worker.run_once()
    assert terminal_duplicate is not None and terminal_duplicate.status == "duplicate"
    assert terminal_duplicate.status != "completed"
    assert isinstance(terminal_duplicate.result, DuplicateCommandError)

    duplicate_queue = InMemoryQueue()
    duplicate_queue.enqueue(command)
    duplicate_queue.enqueue(command)
    assert len(duplicate_queue) == 1

    duplicate_result = BackgroundExecutionResult(
        status="duplicate",
        command=command,
        result=DuplicateCommandError(command.logical_id),
    )
    assert duplicate_result.status == "duplicate"


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (ProviderUnavailableError("unavailable"), True),
        (ProviderTimeoutError("timeout"), True),
        (ProviderResponseError("bad response"), False),
        (ProviderInvalidOutputError("invalid output"), False),
    ],
)
def test_ai_provider_failure_classification(error, retryable):
    assert classify_background_failure(error).retryable is retryable


def test_successful_execution_is_completed_on_first_attempt():
    queue = InMemoryQueue()
    command = CompetitorDiscoveryCommand(research_run_id=31)
    queue.enqueue(command)
    worker = BackgroundWorker(
        queue=queue,
        dispatcher=BackgroundDispatcher(competitor_discovery_service=lambda db, research_run_id: "ok"),
        db_session_factory=lambda: object(),
    )

    result = worker.run_once()

    assert result is not None
    assert result.status == "completed"
    assert result.attempt_count == 1
    assert len(queue) == 0


def test_background_command_logical_id_is_stable_across_retries():
    command_a = CompetitorResearchCommand(research_run_id=42, competitor_ids=[1, 2], max_attempts=4)
    command_b = CompetitorResearchCommand(research_run_id=42, competitor_ids=[1, 2], max_attempts=5)
    retry_command = command_a.with_retry_attempt()

    assert command_a.logical_id == command_b.logical_id
    assert command_a.logical_id == retry_command.logical_id
    assert retry_command.attempt_count == 2
    assert command_a.logical_id == command_a.with_retry_attempt(3).logical_id


def test_competitor_research_logical_id_canonicalizes_ids_without_reordering_command():
    ordered = CompetitorResearchCommand(research_run_id=42, competitor_ids=[1, 2, 3])
    reordered = CompetitorResearchCommand(research_run_id=42, competitor_ids=[3, 1, 2])
    repeated = CompetitorResearchCommand(research_run_id=42, competitor_ids=[3, 1, 2, 2, 1])

    assert ordered.logical_id == reordered.logical_id == repeated.logical_id
    assert reordered.competitor_ids == [3, 1, 2]
    assert repeated.competitor_ids == [3, 1, 2, 2, 1]


def test_research_run_analysis_logical_id_canonicalizes_ids_without_reordering_command():
    ordered_ids = [1, 2, 3]
    reordered_ids = [3, 1, 2, 2]
    ordered = AIAnalysisCommand(
        research_run_id=42,
        scope="research_run",
        provider=FakeAIProvider(),
        competitor_research_ids=ordered_ids,
    )
    reordered = AIAnalysisCommand(
        research_run_id=42,
        scope="research_run",
        provider=FakeAIProvider(),
        competitor_research_ids=reordered_ids,
    )

    assert ordered.logical_id == reordered.logical_id
    assert ordered.competitor_research_ids == ordered_ids
    assert reordered.competitor_research_ids == reordered_ids


def test_different_logical_commands_have_different_logical_ids():
    command_a = CompetitorDiscoveryCommand(research_run_id=42)
    command_b = CompetitorDiscoveryCommand(research_run_id=43)

    assert command_a.logical_id != command_b.logical_id

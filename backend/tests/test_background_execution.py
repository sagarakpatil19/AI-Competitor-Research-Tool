from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.background.commands import (
    AIAnalysisCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue
from app.background.worker import BackgroundWorker


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

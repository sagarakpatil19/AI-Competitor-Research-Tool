from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable

from fastapi import Request
from sqlalchemy import select

from app.ai.providers import GeminiProvider
from app.background.commands import BackgroundCommand, CompetitorResearchCommand, SourceCollectionCommand
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue
from app.background.worker import BackgroundFailure, BackgroundWorker, classify_background_failure
from app.db.session import SessionLocal
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_source import CompetitorSource
from app.models.research_run import ResearchRun
from app.services import research as research_service
from app.services.ai_analysis import execute_ai_analysis_for_background
from app.services.competitor_discovery_run import run_competitor_discovery
from app.services.competitor_research_structuring import structure_competitor_research


@dataclass
class BackgroundOperation:
    command: BackgroundCommand
    operation: str
    research_run_id: int
    status: str
    resource_reference: dict[str, Any]
    attempt_count: int
    max_attempts: int
    result: Any = None
    failure_category: str | None = None
    failure_reason: str | None = None

    @property
    def logical_id(self) -> str:
        return self.command.logical_id


class BackgroundRuntime:
    """Process-local API lifecycle state backed by the existing in-memory worker queue."""

    def __init__(self, db_session_factory: Callable[[], Any] = SessionLocal) -> None:
        self.queue = InMemoryQueue()
        self.dispatcher = BackgroundDispatcher(
            competitor_discovery_service=run_competitor_discovery,
            competitor_research_service=research_service.research_competitors,
            source_collection_service=research_service.collect_competitor_source,
            ai_analysis_service=execute_ai_analysis_for_background,
        )
        self.worker = BackgroundWorker(
            queue=self.queue,
            dispatcher=self.dispatcher,
            db_session_factory=db_session_factory,
        )
        self._operations: dict[str, BackgroundOperation] = {}
        self._state_lock = Lock()
        self._processing_lock = Lock()

    def submit(
        self,
        command: BackgroundCommand,
        *,
        operation: str,
        research_run_id: int,
        resource_reference: dict[str, Any],
    ) -> BackgroundOperation:
        logical_id = command.logical_id
        with self._state_lock:
            existing = self._operations.get(logical_id)
            if existing is not None:
                return existing
            record = BackgroundOperation(
                command=command,
                operation=operation,
                research_run_id=research_run_id,
                status="queued",
                resource_reference=resource_reference,
                attempt_count=command.attempt_count,
                max_attempts=command.max_attempts,
            )
            self._operations[logical_id] = record
            self.queue.enqueue(command)
            return record

    def get_operation(self, logical_id: str) -> BackgroundOperation | None:
        with self._state_lock:
            return self._operations.get(logical_id)

    def process_pending(self) -> None:
        with self._processing_lock:
            initial_commands = list(self.queue)
            attempt_budget = sum(
                command.max_attempts - command.attempt_count + 1
                for command in initial_commands
            )
            while attempt_budget > 0:
                command = next(iter(self.queue), None)
                if command is None:
                    return
                attempt_budget -= 1
                record = self.get_operation(command.logical_id)
                if record is not None:
                    with self._state_lock:
                        record.status = "running"
                        record.attempt_count = command.attempt_count
                try:
                    try:
                        execution = self.worker.run_once()
                    except Exception as exc:
                        if record is not None:
                            failure = classify_background_failure(exc)
                            with self._state_lock:
                                record.status = "failed"
                                record.failure_category = failure.category
                                record.failure_reason = failure.message
                        continue
                    if execution is None or record is None:
                        continue
                    if execution.status == "completed" and isinstance(command, CompetitorResearchCommand):
                        child_ids = self._enqueue_source_collections(execution.result)
                        child_failure = self._drain_source_collections(child_ids)
                        if child_failure is not None:
                            with self._state_lock:
                                record.status = "failed"
                                record.failure_category = child_failure.category
                                record.failure_reason = child_failure.message
                            continue
                        self._structure_unfinished_executions(execution.result)
                    self._apply_execution_result(record, execution)
                except Exception as exc:
                    if record is not None:
                        failure = classify_background_failure(exc)
                        with self._state_lock:
                            record.status = "failed"
                            record.failure_category = failure.category
                            record.failure_reason = failure.message
                    continue

    def _enqueue_source_collections(self, executions: list[Any]) -> list[str]:
        child_ids: list[str] = []
        for execution in executions:
            db = self.worker.db_session_factory()
            try:
                sources = list(
                    db.scalars(
                        select(CompetitorSource).where(
                            CompetitorSource.competitor_research_id == execution.id,
                        )
                    ).all()
                )
                for source in sources:
                    command = SourceCollectionCommand(
                        research_run_id=execution.research_run_id,
                        competitor_id=execution.competitor_id,
                        competitor_research_id=execution.id,
                        source_id=source.id,
                    )
                    record = self.submit(
                        command,
                        operation="source_collection",
                        research_run_id=execution.research_run_id,
                        resource_reference={
                            "competitor_id": execution.competitor_id,
                            "competitor_research_id": execution.id,
                            "source_id": source.id,
                        },
                    )
                    child_ids.append(record.logical_id)
            finally:
                db.close()
        return child_ids

    def _drain_source_collections(self, child_ids: list[str]) -> BackgroundFailure | None:
        while True:
            active = [
                logical_id
                for logical_id in child_ids
                if (record := self.get_operation(logical_id)) is not None
                and record.status in {"queued", "running", "retrying"}
            ]
            if not active:
                return None
            child_execution = self.worker.run_once()
            if child_execution is None:
                return BackgroundFailure(
                    category="source_collection",
                    retryable=False,
                    message="Source collection operation did not execute",
                )
            child_record = self.get_operation(child_execution.logical_id)
            if child_record is not None:
                self._apply_execution_result(child_record, child_execution)

    def _structure_unfinished_executions(self, executions: list[Any]) -> None:
        for execution in executions:
            if execution.status == "completed":
                continue
            db = self.worker.db_session_factory()
            try:
                current_execution = db.get(CompetitorResearch, execution.id)
                if current_execution is None or current_execution.status == "completed":
                    continue
                research_run = db.get(ResearchRun, execution.research_run_id)
                if research_run is None:
                    raise LookupError("Research run not found")
                structure_competitor_research(db, research_run, current_execution.id)
            finally:
                db.close()

    def _apply_execution_result(self, record: BackgroundOperation, execution: Any) -> None:
        with self._state_lock:
            record.attempt_count = execution.attempt_count
            if execution.status == "retry_scheduled":
                record.status = "retrying"
                failure = classify_background_failure(execution.result)
                record.failure_category = failure.category
                record.failure_reason = failure.message
            elif execution.status == "completed":
                record.result = execution.result
                if (
                    record.operation == "competitor_discovery"
                    and getattr(execution.result, "status", None) == "failed"
                ):
                    record.status = "failed"
                    record.failure_category = execution.result.failure_category
                    record.failure_reason = execution.result.failure_reason
                else:
                    record.status = "completed"
                    record.failure_category = None
                    record.failure_reason = None
            elif execution.status == "failed":
                record.status = "failed"
                failure = classify_background_failure(execution.result)
                record.failure_category = failure.category
                record.failure_reason = failure.message


def get_background_runtime(request: Request) -> BackgroundRuntime:
    return request.app.state.background_runtime


def create_ai_provider() -> GeminiProvider:
    return GeminiProvider()
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable

from fastapi import Request

from app.ai.providers import GeminiProvider
from app.background.commands import BackgroundCommand
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue
from app.background.worker import BackgroundWorker, classify_background_failure
from app.db.session import SessionLocal
from app.services import research as research_service
from app.services.ai_analysis import execute_ai_analysis
from app.services.competitor_discovery_run import run_competitor_discovery


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
            ai_analysis_service=execute_ai_analysis,
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
                with self._state_lock:
                    record.attempt_count = execution.attempt_count
                    if execution.status == "retry_scheduled":
                        record.status = "retrying"
                        failure = classify_background_failure(execution.result)
                        record.failure_category = failure.category
                        record.failure_reason = failure.message
                    elif execution.status == "completed":
                        record.status = "completed"
                        record.result = execution.result
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
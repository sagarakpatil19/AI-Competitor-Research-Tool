from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.ai.errors import (
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.background.commands import BackgroundCommand
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import QueueProtocol


@dataclass(frozen=True)
class BackgroundFailure:
    category: str
    retryable: bool
    message: str


class DuplicateCommandError(RuntimeError):
    def __init__(self, logical_id: str) -> None:
        super().__init__(f"Duplicate background command: {logical_id}")
        self.logical_id = logical_id


def classify_background_failure(exc: BaseException) -> BackgroundFailure:
    if isinstance(exc, (ProviderUnavailableError, ProviderTimeoutError)):
        return BackgroundFailure(category=type(exc).__name__.lower(), retryable=True, message=str(exc))
    if isinstance(exc, (ProviderResponseError, ProviderInvalidOutputError)):
        return BackgroundFailure(category=type(exc).__name__.lower(), retryable=False, message=str(exc))
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return BackgroundFailure(category="network", retryable=True, message=str(exc))
    if isinstance(exc, (ValueError, TypeError, LookupError)):
        return BackgroundFailure(category="validation", retryable=False, message=str(exc))
    return BackgroundFailure(category=type(exc).__name__.lower(), retryable=False, message=str(exc))


@dataclass
class BackgroundExecutionResult:
    status: str
    command: BackgroundCommand
    result: Any
    logical_id: str | None = None
    retryable: bool = False
    attempt_count: int = 1
    max_attempts: int = 3


class BackgroundWorker:
    def __init__(
        self,
        *,
        queue: QueueProtocol,
        dispatcher: BackgroundDispatcher,
        db_session_factory: Callable[[], Any],
    ) -> None:
        self.queue = queue
        self.dispatcher = dispatcher
        self.db_session_factory = db_session_factory
        self._inflight_logical_ids: set[str] = set()
        self._terminal_logical_ids: set[str] = set()

    def run_once(self) -> BackgroundExecutionResult | None:
        command = self.queue.dequeue()
        if command is None:
            return None

        logical_id = command.logical_id
        if logical_id in self._inflight_logical_ids or logical_id in self._terminal_logical_ids:
            return BackgroundExecutionResult(
                status="duplicate",
                command=command,
                result=DuplicateCommandError(logical_id),
                logical_id=logical_id,
                retryable=False,
                attempt_count=command.attempt_count,
                max_attempts=command.max_attempts,
            )

        self._inflight_logical_ids.add(logical_id)

        db_session = self.db_session_factory()
        try:
            result = self.dispatcher.dispatch(db_session, command)
            self._terminal_logical_ids.add(logical_id)
            status = "completed"
            return BackgroundExecutionResult(
                status=status,
                command=command,
                result=result,
                logical_id=logical_id,
                retryable=False,
                attempt_count=command.attempt_count,
                max_attempts=command.max_attempts,
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            failure = classify_background_failure(exc)
            if failure.retryable and command.attempt_count < command.max_attempts:
                retry_command = command.with_retry_attempt(command.attempt_count + 1)
                self.queue.enqueue(retry_command)
                return BackgroundExecutionResult(
                    status="retry_scheduled",
                    command=command,
                    result=exc,
                    logical_id=logical_id,
                    retryable=True,
                    attempt_count=command.attempt_count,
                    max_attempts=command.max_attempts,
                )

            self._terminal_logical_ids.add(logical_id)
            return BackgroundExecutionResult(
                status="failed",
                command=command,
                result=exc,
                logical_id=logical_id,
                retryable=failure.retryable,
                attempt_count=command.attempt_count,
                max_attempts=command.max_attempts,
            )
        finally:
            self._inflight_logical_ids.discard(logical_id)
            close = getattr(db_session, "close", None)
            if callable(close):
                close()

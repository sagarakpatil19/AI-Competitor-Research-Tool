from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.background.commands import BackgroundCommand
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import QueueProtocol


@dataclass
class BackgroundExecutionResult:
    status: str
    command: BackgroundCommand
    result: Any


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

    def run_once(self) -> BackgroundExecutionResult | None:
        command = self.queue.dequeue()
        if command is None:
            return None

        db_session = self.db_session_factory()
        try:
            result = self.dispatcher.dispatch(db_session, command)
            status = "completed"
            return BackgroundExecutionResult(status=status, command=command, result=result)
        except Exception as exc:  # pragma: no cover - defensive boundary
            status = "failed"
            return BackgroundExecutionResult(status=status, command=command, result=exc)
        finally:
            close = getattr(db_session, "close", None)
            if callable(close):
                close()

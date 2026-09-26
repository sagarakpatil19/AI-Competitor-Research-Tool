from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

from app.background.commands import BackgroundCommand


class QueueProtocol(Protocol):
    def enqueue(self, command: BackgroundCommand) -> None: ...

    def dequeue(self) -> BackgroundCommand | None: ...


@dataclass
class InMemoryQueue:
    """Simple in-memory queue for local development and testing only."""

    _items: list[BackgroundCommand] = field(default_factory=list)
    _queued_logical_ids: set[str] = field(default_factory=set)

    def enqueue(self, command: BackgroundCommand) -> None:
        logical_id = command.logical_id
        if logical_id in self._queued_logical_ids:
            return
        self._items.append(command)
        self._queued_logical_ids.add(logical_id)

    def dequeue(self) -> BackgroundCommand | None:
        if not self._items:
            return None
        command = self._items.pop(0)
        self._queued_logical_ids.discard(command.logical_id)
        return command

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[BackgroundCommand]:
        return iter(self._items)

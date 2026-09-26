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

    def enqueue(self, command: BackgroundCommand) -> None:
        self._items.append(command)

    def dequeue(self) -> BackgroundCommand | None:
        if not self._items:
            return None
        return self._items.pop(0)

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[BackgroundCommand]:
        return iter(self._items)

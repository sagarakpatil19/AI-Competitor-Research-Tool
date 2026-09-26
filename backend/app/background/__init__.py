"""Background execution primitives for M14-C."""

from app.background.commands import (
    AIAnalysisCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue, QueueProtocol
from app.background.worker import BackgroundExecutionResult, BackgroundWorker

__all__ = [
    "AIAnalysisCommand",
    "BackgroundDispatcher",
    "BackgroundExecutionResult",
    "BackgroundWorker",
    "CompetitorDiscoveryCommand",
    "CompetitorResearchCommand",
    "InMemoryQueue",
    "QueueProtocol",
    "SourceCollectionCommand",
]

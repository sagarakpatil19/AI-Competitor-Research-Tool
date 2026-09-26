"""Background execution primitives for M14-C."""

from app.background.commands import (
    AIAnalysisCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.dispatcher import BackgroundDispatcher
from app.background.queue import InMemoryQueue, QueueProtocol
from app.background.worker import (
    BackgroundExecutionResult,
    BackgroundFailure,
    BackgroundWorker,
    DuplicateCommandError,
    classify_background_failure,
)

__all__ = [
    "AIAnalysisCommand",
    "BackgroundDispatcher",
    "BackgroundExecutionResult",
    "BackgroundFailure",
    "BackgroundWorker",
    "CompetitorDiscoveryCommand",
    "CompetitorResearchCommand",
    "DuplicateCommandError",
    "InMemoryQueue",
    "QueueProtocol",
    "SourceCollectionCommand",
    "classify_background_failure",
]

from typing import Protocol

from app.ai.contracts import ProviderAnalysisResult
from app.context.analysis_context import AnalysisContext


class AIProvider(Protocol):
    def analyze(self, context: AnalysisContext) -> ProviderAnalysisResult:
        """Analyze provider-neutral context without accessing persistence."""
        ...

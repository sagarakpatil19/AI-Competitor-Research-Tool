from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.provider import AIProvider


@dataclass(frozen=True)
class BackgroundCommand:
    """Base background command payload."""

    command_type: str = field(init=False)

    def _validate_positive_int(self, value: int, field_name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class CompetitorDiscoveryCommand(BackgroundCommand):
    research_run_id: int
    command_type: str = field(init=False, default="competitor_discovery")

    def __post_init__(self) -> None:
        self._validate_positive_int(self.research_run_id, "research_run_id")


@dataclass(frozen=True)
class CompetitorResearchCommand(BackgroundCommand):
    research_run_id: int
    competitor_ids: list[int]
    command_type: str = field(init=False, default="competitor_research")

    def __post_init__(self) -> None:
        self._validate_positive_int(self.research_run_id, "research_run_id")
        if not self.competitor_ids:
            raise ValueError("competitor_ids must not be empty")
        for competitor_id in self.competitor_ids:
            self._validate_positive_int(competitor_id, "competitor_id")


@dataclass(frozen=True)
class SourceCollectionCommand(BackgroundCommand):
    research_run_id: int
    competitor_id: int
    competitor_research_id: int
    source_id: int
    command_type: str = field(init=False, default="source_collection")

    def __post_init__(self) -> None:
        self._validate_positive_int(self.research_run_id, "research_run_id")
        self._validate_positive_int(self.competitor_id, "competitor_id")
        self._validate_positive_int(self.competitor_research_id, "competitor_research_id")
        self._validate_positive_int(self.source_id, "source_id")


@dataclass(frozen=True)
class AIAnalysisCommand(BackgroundCommand):
    research_run_id: int
    scope: str
    provider: AIProvider
    contract_version: str = "contract-v1"
    prompt_version: str = "prompt-v1"
    competitor_research_id: int | None = None
    competitor_research_ids: list[int] | None = None
    command_type: str = field(init=False, default="ai_analysis")

    def __post_init__(self) -> None:
        self._validate_positive_int(self.research_run_id, "research_run_id")
        if self.scope not in {"competitor", "research_run"}:
            raise ValueError("scope must be 'competitor' or 'research_run'")
        if self.scope == "competitor":
            if self.competitor_research_id is None:
                raise ValueError("competitor_research_id is required for competitor scope")
            self._validate_positive_int(self.competitor_research_id, "competitor_research_id")
        else:
            if not self.competitor_research_ids:
                raise ValueError("competitor_research_ids is required for research_run scope")
            for competitor_research_id in self.competitor_research_ids:
                self._validate_positive_int(competitor_research_id, "competitor_research_id")

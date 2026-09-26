from __future__ import annotations

from typing import Any, Callable

from app.background.commands import (
    AIAnalysisCommand,
    BackgroundCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.models.research_run import ResearchRun
from app.repositories.research_runs import get_research_run


class BackgroundDispatcher:
    def __init__(
        self,
        *,
        competitor_discovery_service: Callable[[Any, int], Any] | None = None,
        competitor_research_service: Callable[[Any, ResearchRun, list[int]], Any] | None = None,
        source_collection_service: Callable[[Any, ResearchRun, int, int, int | None], Any] | None = None,
        ai_analysis_service: Callable[..., Any] | None = None,
    ) -> None:
        self.competitor_discovery_service = competitor_discovery_service
        self.competitor_research_service = competitor_research_service
        self.source_collection_service = source_collection_service
        self.ai_analysis_service = ai_analysis_service

    def dispatch(self, db_session: Any, command: BackgroundCommand) -> Any:
        if isinstance(command, CompetitorDiscoveryCommand):
            if self.competitor_discovery_service is None:
                raise ValueError("Competitor discovery service is not configured")
            return self.competitor_discovery_service(db_session, command.research_run_id)

        if isinstance(command, CompetitorResearchCommand):
            if self.competitor_research_service is None:
                raise ValueError("Competitor research service is not configured")
            research_run = get_research_run(db_session, command.research_run_id)
            if research_run is None:
                raise LookupError(f"Research run {command.research_run_id} not found")
            return self.competitor_research_service(db_session, research_run, command.competitor_ids)

        if isinstance(command, SourceCollectionCommand):
            if self.source_collection_service is None:
                raise ValueError("Source collection service is not configured")
            research_run = get_research_run(db_session, command.research_run_id)
            if research_run is None:
                raise LookupError(f"Research run {command.research_run_id} not found")
            return self.source_collection_service(
                db_session,
                research_run,
                command.competitor_id,
                command.source_id,
                command.competitor_research_id,
            )

        if isinstance(command, AIAnalysisCommand):
            if self.ai_analysis_service is None:
                raise ValueError("AI analysis service is not configured")
            return self.ai_analysis_service(
                db_session,
                command.research_run_id,
                provider=command.provider,
                scope=command.scope,
                competitor_research_id=command.competitor_research_id,
                competitor_research_ids=command.competitor_research_ids,
                contract_version=command.contract_version,
                prompt_version=command.prompt_version,
            )

        raise ValueError(f"Unsupported command type: {type(command).__name__}")

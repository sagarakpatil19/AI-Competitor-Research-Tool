from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.competitor_discovery_base import (
    CompetitorDiscoveryProvider,
    DiscoveryCompanyContext,
)
from app.integrations.competitor_discovery_base import (
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderResponseError,
    DiscoveryProviderTimeoutError,
)
from app.integrations.tavily_competitor_discovery import TavilyCompetitorDiscoveryProvider
from app.models.company_research import CompanyResearch
from app.models.competitor_discovery_candidate import CompetitorDiscoveryCandidate
from app.models.competitor_discovery_candidate_source import CompetitorDiscoveryCandidateSource
from app.models.competitor_discovery_run import CompetitorDiscoveryRun
from app.models.research_run import ResearchRun
from app.repositories import company_research as company_research_repository
from app.repositories import research_runs as research_run_repository
from app.services.competitor_discovery import (
    DISCOVERY_NORMALIZED,
    VALIDATION_VALID,
    ProcessedDiscoveryCandidate,
    process_discovery_candidates,
)


DISCOVERY_STATUS_PENDING = "pending"
DISCOVERY_STATUS_RUNNING = "running"
DISCOVERY_STATUS_COMPLETED = "completed"
DISCOVERY_STATUS_FAILED = "failed"
DISCOVERY_STATUS_NO_CANDIDATES = "no_candidates"


def run_competitor_discovery(
    db: Session,
    research_run_id: int,
    provider: CompetitorDiscoveryProvider | None = None,
) -> CompetitorDiscoveryRun:
    research_run = research_run_repository.get_research_run(db, research_run_id)
    if research_run is None:
        raise LookupError("Research run not found")

    company_research = company_research_repository.get_by_research_run_id(db, research_run_id)
    provider = provider or TavilyCompetitorDiscoveryProvider()
    provider_name = _provider_name(provider)
    discovery_run = CompetitorDiscoveryRun(
        research_run_id=research_run_id,
        provider_name=provider_name,
        status=DISCOVERY_STATUS_PENDING,
    )
    db.add(discovery_run)
    db.flush()

    discovery_run.status = DISCOVERY_STATUS_RUNNING
    discovery_run.started_at = datetime.now(timezone.utc)

    try:
        context = _company_context(research_run, company_research)
    except ValueError as exc:
        db.rollback()
        return _mark_failed_run(db, discovery_run, "missing_company_context", str(exc))

    try:
        raw_candidates = provider.discover(context)
        processed_candidates = process_discovery_candidates(context, raw_candidates)
        for processed in processed_candidates:
            _add_candidate_rows(db, discovery_run, research_run_id, processed)

        discovery_run.status = (
            DISCOVERY_STATUS_COMPLETED
            if any(item.validation_status == VALIDATION_VALID for item in processed_candidates)
            else DISCOVERY_STATUS_NO_CANDIDATES
        )
        discovery_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(discovery_run)
        return discovery_run
    except DiscoveryProviderError as exc:
        db.rollback()
        _mark_failed_run(
            db,
            discovery_run,
            _provider_failure_category(exc),
            _safe_failure_reason(exc),
        )
        return discovery_run
    except Exception:
        db.rollback()
        raise


def _company_context(
    research_run: ResearchRun,
    company_research: CompanyResearch | None,
) -> DiscoveryCompanyContext:
    if company_research is None:
        raise ValueError("Company understanding is required before competitor discovery")
    return DiscoveryCompanyContext(
        company_name=company_research.company_name or research_run.input_value,
        domain=company_research.domain or research_run.resolved_domain,
        industry=company_research.industry,
        description=company_research.description,
    )


def _provider_name(provider: CompetitorDiscoveryProvider) -> str:
    return str(getattr(provider, "provider_name", provider.__class__.__name__.lower()))[:100]


def _add_candidate_rows(
    db: Session,
    discovery_run: CompetitorDiscoveryRun,
    research_run_id: int,
    processed: ProcessedDiscoveryCandidate,
) -> None:
    candidate_name = processed.candidate_name or processed.domain or "Unknown candidate"
    normalized_name = processed.normalized_name or candidate_name.casefold()
    candidate = CompetitorDiscoveryCandidate(
        discovery_run_id=discovery_run.id,
        research_run_id=research_run_id,
        candidate_name=candidate_name,
        normalized_name=normalized_name,
        domain=processed.domain,
        canonical_url=processed.canonical_url,
        discovery_method=processed.discovery_method,
        provider_name=processed.provider_name,
        provider_candidate_id=processed.provider_candidate_id,
        provider_rank=processed.provider_rank,
        discovery_status=processed.discovery_status,
        validation_status=processed.validation_status,
        validation_reason=processed.validation_reason,
    )
    db.add(candidate)
    db.flush()
    for provenance in processed.supporting_sources:
        db.add(
            CompetitorDiscoveryCandidateSource(
                candidate_id=candidate.id,
                source_url=provenance.supporting_result_url,
                canonical_url=provenance.supporting_result_url,
                source_title=provenance.source_title,
                source_snippet=provenance.source_snippet,
                provider_name=provenance.provider_name,
                provider_result_id=provenance.provider_result_id,
                provider_rank=provenance.provider_rank,
            )
        )


def _provider_failure_category(error: DiscoveryProviderError) -> str:
    if isinstance(error, DiscoveryProviderTimeoutError):
        return "timeout"
    if isinstance(error, DiscoveryProviderRateLimitError):
        return "rate_limit"
    if isinstance(error, DiscoveryProviderAuthenticationError):
        return "authentication"
    if isinstance(error, DiscoveryProviderResponseError):
        return "provider_error"
    return "provider_error"


def _safe_failure_reason(error: DiscoveryProviderError) -> str:
    if isinstance(error, DiscoveryProviderTimeoutError):
        return "Discovery provider timed out"
    if isinstance(error, DiscoveryProviderRateLimitError):
        return "Discovery provider rate limit exceeded"
    if isinstance(error, DiscoveryProviderAuthenticationError):
        return "Discovery provider authentication failed"
    return "Discovery provider request failed"


def _mark_failed_run(
    db: Session,
    discovery_run: CompetitorDiscoveryRun,
    category: str,
    reason: str,
) -> CompetitorDiscoveryRun:
    discovery_run.status = DISCOVERY_STATUS_FAILED
    discovery_run.failure_category = category
    discovery_run.failure_reason = reason
    discovery_run.completed_at = datetime.now(timezone.utc)
    db.add(discovery_run)
    db.commit()
    db.refresh(discovery_run)
    return discovery_run

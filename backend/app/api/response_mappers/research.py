from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.competitor_source import CompetitorSource
from app.schemas.competitor_evidence import CompetitorEvidenceResponse
from app.schemas.competitor_research import CompetitorResearchResponse
from app.schemas.competitor_source import CompetitorSourceResponse


def competitor_research_to_response(
    competitor_research: CompetitorResearch,
) -> CompetitorResearchResponse:
    return CompetitorResearchResponse(
        id=competitor_research.id,
        competitor_id=competitor_research.competitor_id,
        description=competitor_research.description,
        industry=competitor_research.industry,
        products_services=competitor_research.products_services,
        target_customers=competitor_research.target_customers,
        business_model=competitor_research.business_model,
        created_at=competitor_research.created_at,
        updated_at=competitor_research.updated_at,
    )


def competitor_evidence_to_response(
    evidence: CompetitorEvidence,
) -> CompetitorEvidenceResponse:
    return CompetitorEvidenceResponse(
        id=evidence.id,
        competitor_research_id=evidence.competitor_research_id,
        source_id=evidence.source_id,
        source_url=evidence.source_url,
        source_title=evidence.source_title,
        source_type=evidence.source_type,
        publisher=evidence.publisher,
        published_at=evidence.published_at,
        retrieved_at=evidence.retrieved_at,
        content=evidence.content,
        content_excerpt=evidence.content_excerpt,
        processing_status=evidence.processing_status,
        validation_status=evidence.validation_status,
        processing_error=evidence.processing_error,
        validation_reason=evidence.validation_reason,
        normalized_content=evidence.normalized_content,
        normalized_excerpt=evidence.normalized_excerpt,
        normalized_content_hash=evidence.normalized_content_hash,
        processed_at=evidence.processed_at,
        created_at=evidence.created_at,
        updated_at=evidence.updated_at,
    )


def competitor_source_to_response(source: CompetitorSource) -> CompetitorSourceResponse:
    return CompetitorSourceResponse(
        id=source.id,
        competitor_research_id=source.competitor_research_id,
        canonical_url=source.canonical_url,
        source_type=source.source_type,
        discovery_method=source.discovery_method,
        status=source.status,
        attempt_count=source.attempt_count,
        last_http_status=source.last_http_status,
        last_attempted_at=source.last_attempted_at,
        failure_category=source.failure_category,
        failure_reason=source.failure_reason,
        content_hash=source.content_hash,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
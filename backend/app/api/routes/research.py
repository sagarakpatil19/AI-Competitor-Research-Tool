from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company_research import CompanyResearch
from app.models.competitor import Competitor
from app.models.competitor_evidence import CompetitorEvidence
from app.models.competitor_research import CompetitorResearch
from app.models.research_run import ResearchRun
from app.schemas.competitor import DiscoveredCompetitorResponse, DiscoveryRequest
from app.schemas.competitor_evidence import CompetitorEvidenceCreate, CompetitorEvidenceResponse
from app.schemas.competitor_research import CompetitorResearchResponse, CompetitorResearchUpdate
from app.schemas.research import (
    CompanyResearchResponse,
    ResearchCreate,
    ResearchResponse,
    ResearchDiscoverResponse,
    ResearchCompetitorRequest,
    ResearchCompetitorResponse,
    ResearchCompetitorUpdateResponse,
    ResearchEvidenceListResponse,
    ResearchEvidenceResponse,
    ResearchUnderstandResponse,
)
from app.services import research as research_service

router = APIRouter(prefix="/research", tags=["research"])


def to_response(research_run: ResearchRun) -> ResearchResponse:
    return ResearchResponse(
        research_id=research_run.id,
        input_value=research_run.input_value,
        input_type=research_run.input_type,
        resolved_domain=research_run.resolved_domain,
        status=research_run.status,
        created_at=research_run.created_at,
        updated_at=research_run.updated_at,
        completed_at=research_run.completed_at,
        failure_reason=research_run.failure_reason,
    )


def company_research_to_response(company_research: CompanyResearch) -> CompanyResearchResponse:
    return CompanyResearchResponse(
        id=company_research.id,
        research_run_id=company_research.research_run_id,
        company_name=company_research.company_name,
        domain=company_research.domain,
        description=company_research.description,
        industry=company_research.industry,
        created_at=company_research.created_at,
        updated_at=company_research.updated_at,
    )


def competitor_to_discovery_response(competitor: Competitor) -> DiscoveredCompetitorResponse:
    return DiscoveredCompetitorResponse(
        id=competitor.id,
        research_run_id=competitor.research_run_id,
        name=competitor.name,
        domain=competitor.domain,
        created_at=competitor.created_at,
        updated_at=competitor.updated_at,
    )


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
        source_url=evidence.source_url,
        source_title=evidence.source_title,
        source_type=evidence.source_type,
        publisher=evidence.publisher,
        published_at=evidence.published_at,
        retrieved_at=evidence.retrieved_at,
        content=evidence.content,
        content_excerpt=evidence.content_excerpt,
        created_at=evidence.created_at,
        updated_at=evidence.updated_at,
    )


@router.post("", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
def create_research(payload: ResearchCreate, db: Session = Depends(get_db)) -> ResearchResponse:
    try:
        research_run = research_service.create_research_run(db, payload.company)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return to_response(research_run)


@router.get("/{research_id}", response_model=ResearchResponse)
def get_research(research_id: int, db: Session = Depends(get_db)) -> ResearchResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    return to_response(research_run)


@router.post("/{research_id}/resolve", response_model=ResearchResponse)
def resolve_research(research_id: int, db: Session = Depends(get_db)) -> ResearchResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        research_run = research_service.resolve_research_run(db, research_run)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return to_response(research_run)


@router.post("/{research_id}/understand", response_model=ResearchUnderstandResponse)
def understand_research(
    research_id: int,
    db: Session = Depends(get_db),
) -> ResearchUnderstandResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        company_research = research_service.understand_company(db, research_run)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchUnderstandResponse(
        research=to_response(research_run),
        company_research=company_research_to_response(company_research),
    )


@router.post("/{research_id}/discover", response_model=ResearchDiscoverResponse)
def discover_research(
    research_id: int,
    payload: DiscoveryRequest,
    db: Session = Depends(get_db),
) -> ResearchDiscoverResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        competitors = research_service.discover_competitors(db, research_run, payload.competitors)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchDiscoverResponse(
        research=to_response(research_run),
        competitors=[competitor_to_discovery_response(competitor) for competitor in competitors],
    )


@router.post("/{research_id}/research", response_model=ResearchCompetitorResponse)
def research_competitors(
    research_id: int,
    payload: ResearchCompetitorRequest,
    db: Session = Depends(get_db),
) -> ResearchCompetitorResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        competitor_research = research_service.research_competitors(
            db,
            research_run,
            payload.competitor_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchCompetitorResponse(
        research=to_response(research_run),
        competitor_research=[
            competitor_research_to_response(item) for item in competitor_research
        ],
    )


@router.patch(
    "/{research_id}/competitors/{competitor_id}/research",
    response_model=ResearchCompetitorUpdateResponse,
)
def update_research_competitor(
    research_id: int,
    competitor_id: int,
    payload: CompetitorResearchUpdate,
    db: Session = Depends(get_db),
) -> ResearchCompetitorUpdateResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        competitor_research = research_service.update_competitor_research(
            db,
            research_run,
            competitor_id,
            payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchCompetitorUpdateResponse(
        research=to_response(research_run),
        competitor_research=competitor_research_to_response(competitor_research),
    )


@router.post(
    "/{research_id}/competitors/{competitor_id}/research/evidence",
    response_model=ResearchEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_evidence(
    research_id: int,
    competitor_id: int,
    payload: CompetitorEvidenceCreate,
    db: Session = Depends(get_db),
) -> ResearchEvidenceResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        evidence = research_service.create_competitor_evidence(
            db,
            research_run,
            competitor_id,
            payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchEvidenceResponse(
        research=to_response(research_run),
        evidence=competitor_evidence_to_response(evidence),
    )


@router.get(
    "/{research_id}/competitors/{competitor_id}/research/evidence",
    response_model=ResearchEvidenceListResponse,
)
def list_research_evidence(
    research_id: int,
    competitor_id: int,
    db: Session = Depends(get_db),
) -> ResearchEvidenceListResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        evidence = research_service.list_competitor_evidence(db, research_run, competitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchEvidenceListResponse(
        research=to_response(research_run),
        evidence=[competitor_evidence_to_response(item) for item in evidence],
    )

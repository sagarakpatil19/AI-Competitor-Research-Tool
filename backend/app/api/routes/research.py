from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company_research import CompanyResearch
from app.models.competitor import Competitor
from app.models.research_run import ResearchRun
from app.schemas.competitor import DiscoveredCompetitorResponse, DiscoveryRequest
from app.schemas.research import (
    CompanyResearchResponse,
    ResearchCreate,
    ResearchResponse,
    ResearchDiscoverResponse,
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

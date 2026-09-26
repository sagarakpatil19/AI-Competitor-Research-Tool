from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.background.commands import (
    AIAnalysisCommand,
    CompetitorDiscoveryCommand,
    CompetitorResearchCommand,
    SourceCollectionCommand,
)
from app.background.runtime import (
    BackgroundRuntime,
    create_ai_provider,
    get_background_runtime,
)
from app.models.company_research import CompanyResearch
from app.models.competitor import Competitor
from app.models.research_run import ResearchRun
from app.schemas.competitor import DiscoveredCompetitorResponse, DiscoveryRequest
from app.schemas.competitor_evidence import CompetitorEvidenceCreate
from app.schemas.competitor_research import CompetitorResearchUpdate
from app.schemas.competitor_source import CompetitorSourceCreate
from app.schemas.background_operation import AIAnalysisRequest, BackgroundOperationResponse
from app.schemas.research import (
    CompanyResearchResponse,
    ResearchCreate,
    ResearchResponse,
    ResearchDiscoverResponse,
    ResearchCompetitorRequest,
    ResearchCompetitorUpdateResponse,
    ResearchEvidenceListResponse,
    ResearchEvidenceResponse,
    ResearchSourceListResponse,
    ResearchSourceResponse,
    ResearchUnderstandResponse,
)
from app.services import research as research_service
from app.repositories import competitor_research as competitor_research_repository
from app.api.response_mappers.research import (
    competitor_evidence_to_response,
    competitor_research_to_response,
    competitor_source_to_response,
)

from app.api.routes.background_operations import operation_to_response

router = APIRouter(prefix="/research", tags=["research"])

discovery_router = APIRouter(tags=["competitor-discovery"])


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


@discovery_router.post(
    "/research-runs/{research_run_id}/competitor-discovery",
    response_model=BackgroundOperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def discover_competitors_from_provider(
    research_run_id: int,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    runtime: BackgroundRuntime = Depends(get_background_runtime),
) -> BackgroundOperationResponse:
    research_run = research_service.get_research_run(db, research_run_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    return _enqueue_operation(
        background_tasks,
        response,
        command=CompetitorDiscoveryCommand(research_run_id=research_run_id),
        operation="competitor_discovery",
        research_run_id=research_run_id,
        resource_reference={"research_run_id": research_run_id},
        runtime=runtime,
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


@router.post("/{research_id}/research", response_model=BackgroundOperationResponse, status_code=status.HTTP_202_ACCEPTED)
def research_competitors(
    research_id: int,
    payload: ResearchCompetitorRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    runtime: BackgroundRuntime = Depends(get_background_runtime),
) -> BackgroundOperationResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        competitor_ids = research_service.validate_research_competitors(db, research_run, payload.competitor_ids)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _enqueue_operation(
        background_tasks,
        response,
        command=CompetitorResearchCommand(research_run_id=research_id, competitor_ids=competitor_ids),
        operation="competitor_research",
        research_run_id=research_id,
        resource_reference={"competitor_ids": competitor_ids},
        runtime=runtime,
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


@router.post(
    "/{research_id}/competitors/{competitor_id}/research/evidence/{evidence_id}/process",
    response_model=ResearchEvidenceResponse,
)
def process_research_evidence(
    research_id: int,
    competitor_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
) -> ResearchEvidenceResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        evidence = research_service.process_competitor_evidence(
            db,
            research_run,
            competitor_id,
            evidence_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchEvidenceResponse(
        research=to_response(research_run),
        evidence=competitor_evidence_to_response(evidence),
    )


@router.post(
    "/{research_id}/competitors/{competitor_id}/research/sources",
    response_model=ResearchSourceResponse,
)
def register_research_source(
    research_id: int,
    competitor_id: int,
    response: Response,
    payload: CompetitorSourceCreate,
    db: Session = Depends(get_db),
) -> ResearchSourceResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        source, created = research_service.register_competitor_source(
            db,
            research_run,
            competitor_id,
            payload.model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    response_body = ResearchSourceResponse(
        research=to_response(research_run),
        source=competitor_source_to_response(source),
    )
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return response_body


@router.get(
    "/{research_id}/competitors/{competitor_id}/research/sources",
    response_model=ResearchSourceListResponse,
)
def list_research_sources(
    research_id: int,
    competitor_id: int,
    db: Session = Depends(get_db),
) -> ResearchSourceListResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        sources = research_service.list_competitor_sources(db, research_run, competitor_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ResearchSourceListResponse(
        research=to_response(research_run),
        sources=[competitor_source_to_response(source) for source in sources],
    )


@router.post(
    "/{research_id}/competitors/{competitor_id}/research/sources/{source_id}/collect",
    response_model=BackgroundOperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def collect_research_source(
    research_id: int,
    competitor_id: int,
    source_id: int,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    runtime: BackgroundRuntime = Depends(get_background_runtime),
) -> BackgroundOperationResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    try:
        competitor_research, _ = research_service.get_source_collection_target(
            db,
            research_run,
            competitor_id,
            source_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _enqueue_operation(
        background_tasks,
        response,
        command=SourceCollectionCommand(
            research_run_id=research_id,
            competitor_id=competitor_id,
            competitor_research_id=competitor_research.id,
            source_id=source_id,
        ),
        operation="source_collection",
        research_run_id=research_id,
        resource_reference={
            "competitor_id": competitor_id,
            "competitor_research_id": competitor_research.id,
            "source_id": source_id,
        },
        runtime=runtime,
    )


@router.post(
    "/{research_id}/ai-analysis",
    response_model=BackgroundOperationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_ai_analysis(
    research_id: int,
    payload: AIAnalysisRequest,
    background_tasks: BackgroundTasks,
    response: Response,
    db: Session = Depends(get_db),
    runtime: BackgroundRuntime = Depends(get_background_runtime),
) -> BackgroundOperationResponse:
    research_run = research_service.get_research_run(db, research_id)
    if research_run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Research run not found")
    selected_ids = (
        [payload.competitor_research_id]
        if payload.scope == "competitor" and payload.competitor_research_id is not None
        else payload.competitor_research_ids or []
    )
    executions = competitor_research_repository.get_by_ids(db, selected_ids)
    if len(executions) != len(set(selected_ids)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor research execution not found")
    if any(item.research_run_id != research_id for item in executions):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Competitor research execution must belong to the research run")
    try:
        command = AIAnalysisCommand(
            research_run_id=research_id,
            scope=payload.scope,
            provider=create_ai_provider(),
            competitor_research_id=payload.competitor_research_id,
            competitor_research_ids=payload.competitor_research_ids,
            contract_version=payload.contract_version,
            prompt_version=payload.prompt_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    resource_reference: dict[str, object] = {"scope": payload.scope}
    if payload.scope == "competitor":
        resource_reference["competitor_research_id"] = payload.competitor_research_id
    else:
        resource_reference["competitor_research_ids"] = payload.competitor_research_ids or []
    return _enqueue_operation(
        background_tasks,
        response,
        command=command,
        operation="ai_analysis",
        research_run_id=research_id,
        resource_reference=resource_reference,
        runtime=runtime,
    )


def _enqueue_operation(
    background_tasks: BackgroundTasks,
    response: Response,
    *,
    command,
    operation: str,
    research_run_id: int,
    resource_reference: dict[str, object],
    runtime: BackgroundRuntime | None = None,
) -> BackgroundOperationResponse:
    if runtime is None:
        raise RuntimeError("Background runtime dependency is required")
    record = runtime.submit(
        command,
        operation=operation,
        research_run_id=research_run_id,
        resource_reference=resource_reference,
    )
    response.headers["Location"] = f"/api/background-operations/{record.logical_id}"
    background_tasks.add_task(runtime.process_pending)
    return operation_to_response(record)

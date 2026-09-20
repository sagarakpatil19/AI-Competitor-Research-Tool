from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.research_run import ResearchRun
from app.schemas.research import ResearchCreate, ResearchResponse
from app.services import research as research_service

router = APIRouter(prefix="/research", tags=["research"])


def to_response(research_run: ResearchRun) -> ResearchResponse:
    return ResearchResponse(
        research_id=research_run.id,
        input_value=research_run.input_value,
        status=research_run.status,
        created_at=research_run.created_at,
        updated_at=research_run.updated_at,
        completed_at=research_run.completed_at,
        failure_reason=research_run.failure_reason,
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
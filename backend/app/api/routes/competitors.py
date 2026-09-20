from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.competitor import Competitor
from app.repositories import competitors as competitor_repository
from app.repositories import projects as project_repository
from app.schemas.competitor import CompetitorCreate, CompetitorResponse, CompetitorUpdate

project_router = APIRouter(prefix="/projects/{project_id}/competitors", tags=["competitors"])
competitor_router = APIRouter(prefix="/competitors", tags=["competitors"])


def require_project(db: Session, project_id: int) -> None:
    if project_repository.get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@project_router.get("", response_model=list[CompetitorResponse])
def list_competitors(project_id: int, db: Session = Depends(get_db)) -> list[Competitor]:
    require_project(db, project_id)
    return competitor_repository.list_competitors(db, project_id)


@project_router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(project_id: int, payload: CompetitorCreate, db: Session = Depends(get_db)) -> Competitor:
    require_project(db, project_id)
    return competitor_repository.create_competitor(db, Competitor(project_id=project_id, **payload.model_dump()))


@competitor_router.get("/{competitor_id}", response_model=CompetitorResponse)
def get_competitor(competitor_id: int, db: Session = Depends(get_db)) -> Competitor:
    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return competitor


@competitor_router.patch("/{competitor_id}", response_model=CompetitorResponse)
def update_competitor(competitor_id: int, payload: CompetitorUpdate, db: Session = Depends(get_db)) -> Competitor:
    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(competitor, field, value)
    return competitor_repository.save_competitor(db, competitor)


@competitor_router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competitor(competitor_id: int, db: Session = Depends(get_db)) -> None:
    competitor = competitor_repository.get_competitor(db, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    competitor_repository.delete_competitor(db, competitor)

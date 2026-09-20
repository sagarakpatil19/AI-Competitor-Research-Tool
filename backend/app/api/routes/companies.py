from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.company import Company
from app.repositories import companies as company_repository
from app.repositories import projects as project_repository
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/projects/{project_id}/company", tags=["company"])


def require_project(db: Session, project_id: int) -> None:
    if project_repository.get_project(db, project_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(project_id: int, payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    require_project(db, project_id)
    if company_repository.get_company(db, project_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project already has a primary company")
    company = Company(project_id=project_id, **payload.model_dump())
    try:
        return company_repository.create_company(db, company)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project already has a primary company") from None


@router.get("", response_model=CompanyResponse)
def get_company(project_id: int, db: Session = Depends(get_db)) -> Company:
    require_project(db, project_id)
    company = company_repository.get_company(db, project_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.patch("", response_model=CompanyResponse)
def update_company(project_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)) -> Company:
    require_project(db, project_id)
    company = company_repository.get_company(db, project_id)
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    return company_repository.save_company(db, company)

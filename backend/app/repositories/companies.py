from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


def get_company(db: Session, project_id: int) -> Company | None:
    return db.scalar(select(Company).where(Company.project_id == project_id))


def create_company(db: Session, company: Company) -> Company:
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def save_company(db: Session, company: Company) -> Company:
    db.commit()
    db.refresh(company)
    return company

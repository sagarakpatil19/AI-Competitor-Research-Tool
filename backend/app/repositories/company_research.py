from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company_research import CompanyResearch


def get_by_research_run_id(db: Session, research_run_id: int) -> CompanyResearch | None:
    return db.scalar(
        select(CompanyResearch).where(CompanyResearch.research_run_id == research_run_id)
    )


def create_company_research(db: Session, company_research: CompanyResearch) -> CompanyResearch:
    db.add(company_research)
    db.commit()
    db.refresh(company_research)
    return company_research


def save_company_research(db: Session, company_research: CompanyResearch) -> CompanyResearch:
    db.commit()
    db.refresh(company_research)
    return company_research
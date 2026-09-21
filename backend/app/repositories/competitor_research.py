from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_research import CompetitorResearch


def get_by_competitor_id(db: Session, competitor_id: int) -> CompetitorResearch | None:
    return db.scalar(
        select(CompetitorResearch)
        .where(CompetitorResearch.competitor_id == competitor_id)
        .order_by(CompetitorResearch.created_at.desc(), CompetitorResearch.id.desc())
    )


def get_by_competitor_ids(
    db: Session,
    competitor_ids: list[int],
) -> list[CompetitorResearch]:
    executions = list(
        db.scalars(
            select(CompetitorResearch)
            .where(CompetitorResearch.competitor_id.in_(competitor_ids))
            .order_by(CompetitorResearch.created_at.desc(), CompetitorResearch.id.desc())
        ).all()
    )
    latest_by_competitor_id: dict[int, CompetitorResearch] = {}
    for execution in executions:
        latest_by_competitor_id.setdefault(execution.competitor_id, execution)
    return list(latest_by_competitor_id.values())


def get_by_ids(db: Session, competitor_research_ids: list[int]) -> list[CompetitorResearch]:
    return list(
        db.scalars(
            select(CompetitorResearch)
            .where(CompetitorResearch.id.in_(competitor_research_ids))
            .order_by(CompetitorResearch.id.asc())
        ).all()
    )


def create_competitor_research(
    db: Session,
    competitor_research: CompetitorResearch,
) -> CompetitorResearch:
    db.add(competitor_research)
    db.commit()
    db.refresh(competitor_research)
    return competitor_research


def save_competitor_research(
    db: Session,
    competitor_research: CompetitorResearch,
) -> CompetitorResearch:
    db.commit()
    db.refresh(competitor_research)
    return competitor_research
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_research import CompetitorResearch


def get_by_competitor_id(db: Session, competitor_id: int) -> CompetitorResearch | None:
    return db.scalar(
        select(CompetitorResearch).where(CompetitorResearch.competitor_id == competitor_id)
    )


def get_by_competitor_ids(
    db: Session,
    competitor_ids: list[int],
) -> list[CompetitorResearch]:
    return list(
        db.scalars(
            select(CompetitorResearch).where(CompetitorResearch.competitor_id.in_(competitor_ids))
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
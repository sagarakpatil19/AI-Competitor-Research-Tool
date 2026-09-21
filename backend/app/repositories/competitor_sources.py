from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_source import CompetitorSource


def get_source(db: Session, source_id: int) -> CompetitorSource | None:
    return db.get(CompetitorSource, source_id)


def get_by_ids(db: Session, source_ids: list[int]) -> list[CompetitorSource]:
    return list(db.scalars(select(CompetitorSource).where(CompetitorSource.id.in_(source_ids))).all())


def get_by_competitor_research_id(
    db: Session,
    competitor_research_id: int,
) -> list[CompetitorSource]:
    return list(
        db.scalars(
            select(CompetitorSource)
            .where(CompetitorSource.competitor_research_id == competitor_research_id)
            .order_by(CompetitorSource.created_at.asc(), CompetitorSource.id.asc())
        ).all()
    )


def get_by_canonical_url(
    db: Session,
    competitor_research_id: int,
    canonical_url: str,
) -> CompetitorSource | None:
    return db.scalar(
        select(CompetitorSource).where(
            CompetitorSource.competitor_research_id == competitor_research_id,
            CompetitorSource.canonical_url == canonical_url,
        )
    )


def create_source(db: Session, source: CompetitorSource) -> CompetitorSource:
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def save_source(db: Session, source: CompetitorSource) -> CompetitorSource:
    db.commit()
    db.refresh(source)
    return source
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_research_fact import CompetitorResearchFact


def get_fact(db: Session, fact_id: int) -> CompetitorResearchFact | None:
    return db.get(CompetitorResearchFact, fact_id)


def list_by_competitor_research_id(
    db: Session,
    competitor_research_id: int,
) -> list[CompetitorResearchFact]:
    return list(
        db.scalars(
            select(CompetitorResearchFact)
            .where(CompetitorResearchFact.competitor_research_id == competitor_research_id)
            .order_by(CompetitorResearchFact.created_at.asc(), CompetitorResearchFact.id.asc())
        ).all()
    )



def list_by_competitor_research_ids(
    db: Session,
    competitor_research_ids: list[int],
) -> list[CompetitorResearchFact]:
    return list(
        db.scalars(
            select(CompetitorResearchFact)
            .where(CompetitorResearchFact.competitor_research_id.in_(competitor_research_ids))
            .order_by(CompetitorResearchFact.competitor_research_id.asc(), CompetitorResearchFact.id.asc())
        ).all()
    )


def create_fact(db: Session, fact: CompetitorResearchFact) -> CompetitorResearchFact:
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact

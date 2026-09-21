from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_comparison_competitor import AIComparisonCompetitor


def list_by_comparison_id(db: Session, comparison_id: int) -> list[AIComparisonCompetitor]:
    return list(
        db.scalars(
            select(AIComparisonCompetitor)
            .where(AIComparisonCompetitor.comparison_id == comparison_id)
            .order_by(AIComparisonCompetitor.created_at.asc())
        ).all()
    )


def create_comparison_competitor(
    db: Session,
    link: AIComparisonCompetitor,
) -> AIComparisonCompetitor:
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

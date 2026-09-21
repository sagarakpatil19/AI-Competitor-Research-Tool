from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_comparison import AIComparison


def get_comparison(db: Session, comparison_id: int) -> AIComparison | None:
    return db.get(AIComparison, comparison_id)


def list_by_analysis_id(db: Session, analysis_id: int) -> list[AIComparison]:
    return list(
        db.scalars(
            select(AIComparison)
            .where(AIComparison.analysis_id == analysis_id)
            .order_by(AIComparison.created_at.asc(), AIComparison.id.asc())
        ).all()
    )


def create_comparison(db: Session, comparison: AIComparison) -> AIComparison:
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison

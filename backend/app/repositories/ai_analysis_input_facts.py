from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis_input_fact import AIAnalysisInputFact


def list_by_analysis_id(db: Session, analysis_id: int) -> list[AIAnalysisInputFact]:
    return list(
        db.scalars(
            select(AIAnalysisInputFact)
            .where(AIAnalysisInputFact.analysis_id == analysis_id)
            .order_by(AIAnalysisInputFact.created_at.asc())
        ).all()
    )


def create_input_fact(db: Session, input_fact: AIAnalysisInputFact) -> AIAnalysisInputFact:
    db.add(input_fact)
    db.commit()
    db.refresh(input_fact)
    return input_fact

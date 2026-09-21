from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis


def get_analysis(db: Session, analysis_id: int) -> AIAnalysis | None:
    return db.get(AIAnalysis, analysis_id)


def list_by_research_run_id(db: Session, research_run_id: int) -> list[AIAnalysis]:
    return list(
        db.scalars(
            select(AIAnalysis)
            .where(AIAnalysis.research_run_id == research_run_id)
            .order_by(AIAnalysis.created_at.asc(), AIAnalysis.id.asc())
        ).all()
    )


def create_analysis(db: Session, analysis: AIAnalysis) -> AIAnalysis:
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def save_analysis(db: Session, analysis: AIAnalysis) -> AIAnalysis:
    db.commit()
    db.refresh(analysis)
    return analysis

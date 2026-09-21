from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis_input_evidence import AIAnalysisInputEvidence


def list_by_analysis_id(db: Session, analysis_id: int) -> list[AIAnalysisInputEvidence]:
    return list(
        db.scalars(
            select(AIAnalysisInputEvidence)
            .where(AIAnalysisInputEvidence.analysis_id == analysis_id)
            .order_by(AIAnalysisInputEvidence.created_at.asc())
        ).all()
    )


def create_input_evidence(db: Session, input_evidence: AIAnalysisInputEvidence) -> AIAnalysisInputEvidence:
    db.add(input_evidence)
    db.commit()
    db.refresh(input_evidence)
    return input_evidence

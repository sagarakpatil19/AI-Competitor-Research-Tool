from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_statement_evidence import AIStatementEvidence


def list_by_statement_id(db: Session, statement_id: int) -> list[AIStatementEvidence]:
    return list(
        db.scalars(
            select(AIStatementEvidence)
            .where(AIStatementEvidence.statement_id == statement_id)
            .order_by(AIStatementEvidence.created_at.asc())
        ).all()
    )


def create_statement_evidence(db: Session, link: AIStatementEvidence) -> AIStatementEvidence:
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

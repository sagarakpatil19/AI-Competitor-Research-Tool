from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_statement_fact import AIStatementFact


def list_by_statement_id(db: Session, statement_id: int) -> list[AIStatementFact]:
    return list(
        db.scalars(
            select(AIStatementFact)
            .where(AIStatementFact.statement_id == statement_id)
            .order_by(AIStatementFact.created_at.asc())
        ).all()
    )


def create_statement_fact(db: Session, link: AIStatementFact) -> AIStatementFact:
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_statement import AIStatement


def get_statement(db: Session, statement_id: int) -> AIStatement | None:
    return db.get(AIStatement, statement_id)


def list_by_analysis_id(db: Session, analysis_id: int) -> list[AIStatement]:
    return list(
        db.scalars(
            select(AIStatement)
            .where(AIStatement.analysis_id == analysis_id)
            .order_by(AIStatement.created_at.asc(), AIStatement.id.asc())
        ).all()
    )


def create_statement(db: Session, statement: AIStatement) -> AIStatement:
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return statement

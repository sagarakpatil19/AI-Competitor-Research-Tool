from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_evidence import CompetitorEvidence


def get_by_source_id(db: Session, source_id: int) -> list[CompetitorEvidence]:
    return list(
        db.scalars(
            select(CompetitorEvidence)
            .where(CompetitorEvidence.source_id == source_id)
            .order_by(CompetitorEvidence.created_at.asc(), CompetitorEvidence.id.asc())
        ).all()
    )


def list_by_competitor_research_id(
    db: Session,
    competitor_research_id: int,
) -> list[CompetitorEvidence]:
    return list(
        db.scalars(
            select(CompetitorEvidence)
            .where(CompetitorEvidence.competitor_research_id == competitor_research_id)
            .order_by(CompetitorEvidence.created_at.asc(), CompetitorEvidence.id.asc())
        ).all()
    )


def create_evidence(db: Session, evidence: CompetitorEvidence) -> CompetitorEvidence:
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def save_evidence(db: Session, evidence: CompetitorEvidence) -> CompetitorEvidence:
    db.commit()
    db.refresh(evidence)
    return evidence
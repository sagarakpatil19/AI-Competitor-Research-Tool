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


def get_evidence(db: Session, evidence_id: int) -> CompetitorEvidence | None:
    return db.get(CompetitorEvidence, evidence_id)


def get_by_id_and_competitor_research_id(
    db: Session,
    evidence_id: int,
    competitor_research_id: int,
) -> CompetitorEvidence | None:
    return db.scalar(
        select(CompetitorEvidence).where(
            CompetitorEvidence.id == evidence_id,
            CompetitorEvidence.competitor_research_id == competitor_research_id,
        )
    )


def get_by_normalized_hash(
    db: Session,
    competitor_research_id: int,
    normalized_content_hash: str,
    exclude_evidence_id: int | None = None,
) -> CompetitorEvidence | None:
    statement = select(CompetitorEvidence).where(
        CompetitorEvidence.competitor_research_id == competitor_research_id,
        CompetitorEvidence.normalized_content_hash == normalized_content_hash,
        CompetitorEvidence.validation_status != "duplicate",
    )
    if exclude_evidence_id is not None:
        statement = statement.where(CompetitorEvidence.id != exclude_evidence_id)
    return db.scalar(statement.order_by(CompetitorEvidence.id.asc()))


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



def list_by_competitor_research_ids(
    db: Session,
    competitor_research_ids: list[int],
) -> list[CompetitorEvidence]:
    return list(
        db.scalars(
            select(CompetitorEvidence)
            .where(CompetitorEvidence.competitor_research_id.in_(competitor_research_ids))
            .order_by(CompetitorEvidence.competitor_research_id.asc(), CompetitorEvidence.id.asc())
        ).all()
    )


def get_by_ids(db: Session, evidence_ids: list[int]) -> list[CompetitorEvidence]:
    return list(db.scalars(select(CompetitorEvidence).where(CompetitorEvidence.id.in_(evidence_ids))).all())


def create_evidence(db: Session, evidence: CompetitorEvidence) -> CompetitorEvidence:
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def save_evidence(db: Session, evidence: CompetitorEvidence) -> CompetitorEvidence:
    db.commit()
    db.refresh(evidence)
    return evidence
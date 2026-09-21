from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_discovery_candidate_source import CompetitorDiscoveryCandidateSource


def get_candidate_source(
    db: Session,
    candidate_source_id: int,
) -> CompetitorDiscoveryCandidateSource | None:
    return db.get(CompetitorDiscoveryCandidateSource, candidate_source_id)


def list_by_candidate_id(
    db: Session,
    candidate_id: int,
) -> list[CompetitorDiscoveryCandidateSource]:
    return list(
        db.scalars(
            select(CompetitorDiscoveryCandidateSource)
            .where(CompetitorDiscoveryCandidateSource.candidate_id == candidate_id)
            .order_by(
                CompetitorDiscoveryCandidateSource.created_at.asc(),
                CompetitorDiscoveryCandidateSource.id.asc(),
            )
        ).all()
    )


def get_by_candidate_id_and_canonical_url(
    db: Session,
    candidate_id: int,
    canonical_url: str,
) -> CompetitorDiscoveryCandidateSource | None:
    return db.scalar(
        select(CompetitorDiscoveryCandidateSource).where(
            CompetitorDiscoveryCandidateSource.candidate_id == candidate_id,
            CompetitorDiscoveryCandidateSource.canonical_url == canonical_url,
        )
    )


def create_candidate_source(
    db: Session,
    candidate_source: CompetitorDiscoveryCandidateSource,
) -> CompetitorDiscoveryCandidateSource:
    db.add(candidate_source)
    db.commit()
    db.refresh(candidate_source)
    return candidate_source

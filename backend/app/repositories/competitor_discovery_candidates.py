from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_discovery_candidate import CompetitorDiscoveryCandidate


def get_candidate(db: Session, candidate_id: int) -> CompetitorDiscoveryCandidate | None:
    return db.get(CompetitorDiscoveryCandidate, candidate_id)


def get_by_id_and_research_run_id(
    db: Session,
    candidate_id: int,
    research_run_id: int,
) -> CompetitorDiscoveryCandidate | None:
    return db.scalar(
        select(CompetitorDiscoveryCandidate).where(
            CompetitorDiscoveryCandidate.id == candidate_id,
            CompetitorDiscoveryCandidate.research_run_id == research_run_id,
        )
    )


def list_by_research_run_id(
    db: Session,
    research_run_id: int,
) -> list[CompetitorDiscoveryCandidate]:
    return list(
        db.scalars(
            select(CompetitorDiscoveryCandidate)
            .where(CompetitorDiscoveryCandidate.research_run_id == research_run_id)
            .order_by(CompetitorDiscoveryCandidate.created_at.asc(), CompetitorDiscoveryCandidate.id.asc())
        ).all()
    )


def get_by_research_run_id_and_domain(
    db: Session,
    research_run_id: int,
    domain: str,
) -> CompetitorDiscoveryCandidate | None:
    return db.scalar(
        select(CompetitorDiscoveryCandidate).where(
            CompetitorDiscoveryCandidate.research_run_id == research_run_id,
            CompetitorDiscoveryCandidate.domain == domain,
        )
    )


def create_candidate(
    db: Session,
    candidate: CompetitorDiscoveryCandidate,
) -> CompetitorDiscoveryCandidate:
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def save_candidate(
    db: Session,
    candidate: CompetitorDiscoveryCandidate,
) -> CompetitorDiscoveryCandidate:
    db.commit()
    db.refresh(candidate)
    return candidate

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_research_fact_evidence import CompetitorResearchFactEvidence


def get_link(
    db: Session,
    fact_id: int,
    evidence_id: int,
) -> CompetitorResearchFactEvidence | None:
    return db.scalar(
        select(CompetitorResearchFactEvidence).where(
            CompetitorResearchFactEvidence.fact_id == fact_id,
            CompetitorResearchFactEvidence.evidence_id == evidence_id,
        )
    )


def create_link(
    db: Session,
    link: CompetitorResearchFactEvidence,
) -> CompetitorResearchFactEvidence:
    db.add(link)
    db.flush()
    return link

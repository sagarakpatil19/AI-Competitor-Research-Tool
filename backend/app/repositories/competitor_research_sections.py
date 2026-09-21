from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_research_section import CompetitorResearchSection


def get_section(db: Session, section_id: int) -> CompetitorResearchSection | None:
    return db.get(CompetitorResearchSection, section_id)


def list_by_competitor_research_id(
    db: Session,
    competitor_research_id: int,
) -> list[CompetitorResearchSection]:
    return list(
        db.scalars(
            select(CompetitorResearchSection)
            .where(CompetitorResearchSection.competitor_research_id == competitor_research_id)
            .order_by(CompetitorResearchSection.id.asc())
        ).all()
    )


def create_section(db: Session, section: CompetitorResearchSection) -> CompetitorResearchSection:
    db.add(section)
    db.commit()
    db.refresh(section)
    return section

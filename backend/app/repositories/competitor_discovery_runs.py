from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_discovery_run import CompetitorDiscoveryRun


def get_discovery_run(db: Session, discovery_run_id: int) -> CompetitorDiscoveryRun | None:
    return db.get(CompetitorDiscoveryRun, discovery_run_id)


def list_by_research_run_id(db: Session, research_run_id: int) -> list[CompetitorDiscoveryRun]:
    return list(
        db.scalars(
            select(CompetitorDiscoveryRun)
            .where(CompetitorDiscoveryRun.research_run_id == research_run_id)
            .order_by(CompetitorDiscoveryRun.created_at.asc(), CompetitorDiscoveryRun.id.asc())
        ).all()
    )


def create_discovery_run(db: Session, discovery_run: CompetitorDiscoveryRun) -> CompetitorDiscoveryRun:
    db.add(discovery_run)
    db.commit()
    db.refresh(discovery_run)
    return discovery_run


def save_discovery_run(db: Session, discovery_run: CompetitorDiscoveryRun) -> CompetitorDiscoveryRun:
    db.commit()
    db.refresh(discovery_run)
    return discovery_run

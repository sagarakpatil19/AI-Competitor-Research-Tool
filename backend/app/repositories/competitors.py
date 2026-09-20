from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor import Competitor


def list_competitors(db: Session, project_id: int) -> list[Competitor]:
    return list(db.scalars(select(Competitor).where(Competitor.project_id == project_id).order_by(Competitor.created_at.desc())).all())


def get_competitor(db: Session, competitor_id: int) -> Competitor | None:
    return db.get(Competitor, competitor_id)


def create_competitor(db: Session, competitor: Competitor) -> Competitor:
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


def save_competitor(db: Session, competitor: Competitor) -> Competitor:
    db.commit()
    db.refresh(competitor)
    return competitor


def delete_competitor(db: Session, competitor: Competitor) -> None:
    db.delete(competitor)
    db.commit()

from sqlalchemy.orm import Session

from app.models.research_run import ResearchRun


def get_research_run(db: Session, research_id: int) -> ResearchRun | None:
    return db.get(ResearchRun, research_id)


def create_research_run(db: Session, research_run: ResearchRun) -> ResearchRun:
    db.add(research_run)
    db.commit()
    db.refresh(research_run)
    return research_run


def save_research_run(db: Session, research_run: ResearchRun) -> ResearchRun:
    db.commit()
    db.refresh(research_run)
    return research_run
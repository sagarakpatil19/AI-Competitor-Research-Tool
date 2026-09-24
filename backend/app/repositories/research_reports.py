from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.research_report import ResearchReport


def get_report(db: Session, report_id: int) -> ResearchReport | None:
    return db.get(ResearchReport, report_id)


def list_by_research_run_id(db: Session, research_run_id: int) -> list[ResearchReport]:
    return list(
        db.scalars(
            select(ResearchReport)
            .where(ResearchReport.research_run_id == research_run_id)
            .order_by(ResearchReport.version.asc(), ResearchReport.id.asc())
        ).all()
    )


def next_version(db: Session, research_run_id: int) -> int:
    current = db.scalar(
        select(func.max(ResearchReport.version)).where(
            ResearchReport.research_run_id == research_run_id
        )
    )
    return (current or 0) + 1


def create_report(db: Session, report: ResearchReport) -> ResearchReport:
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def save_report(db: Session, report: ResearchReport) -> ResearchReport:
    db.commit()
    db.refresh(report)
    return report

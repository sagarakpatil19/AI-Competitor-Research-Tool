from sqlalchemy.orm import Session

from app.models.research_run import ResearchRun, ResearchRunStatus
from app.repositories import research_runs as research_run_repository


def create_research_run(db: Session, input_value: str) -> ResearchRun:
    normalized_input = input_value.strip()
    if not normalized_input:
        raise ValueError("Company name or URL must not be empty")

    research_run = ResearchRun(
        input_value=normalized_input,
        status=ResearchRunStatus.SUBMITTED,
    )
    return research_run_repository.create_research_run(db, research_run)


def get_research_run(db: Session, research_id: int) -> ResearchRun | None:
    return research_run_repository.get_research_run(db, research_id)
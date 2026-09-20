from datetime import datetime

from pydantic import BaseModel, Field

from app.models.research_run import ResearchInputType, ResearchRunStatus


class ResearchCreate(BaseModel):
    company: str = Field(min_length=1, max_length=2048)


class ResearchResponse(BaseModel):
    research_id: int
    input_value: str
    input_type: ResearchInputType | None
    resolved_domain: str | None
    status: ResearchRunStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    failure_reason: str | None
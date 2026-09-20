from datetime import datetime

from pydantic import BaseModel, Field

from app.models.research_run import ResearchInputType, ResearchRunStatus
from app.schemas.competitor import DiscoveredCompetitorResponse


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


class CompanyResearchResponse(BaseModel):
    id: int
    research_run_id: int
    company_name: str | None
    domain: str | None
    description: str | None
    industry: str | None
    created_at: datetime
    updated_at: datetime


class ResearchUnderstandResponse(BaseModel):
    research: ResearchResponse
    company_research: CompanyResearchResponse


class ResearchDiscoverResponse(BaseModel):
    research: ResearchResponse
    competitors: list[DiscoveredCompetitorResponse]
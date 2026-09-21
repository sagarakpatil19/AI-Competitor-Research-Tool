from datetime import datetime

from pydantic import BaseModel, Field


class CompetitorResearchSectionResponse(BaseModel):
    id: int
    competitor_research_id: int
    section: str = Field(max_length=32)
    status: str = Field(max_length=32)
    reason: str | None
    fact_count: int
    created_at: datetime
    updated_at: datetime

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CompetitorSourceCreate(BaseModel):
    source_url: HttpUrl
    source_type: str | None = Field(default=None, max_length=100)
    discovery_method: str | None = Field(default=None, max_length=100)


class CompetitorSourceResponse(BaseModel):
    id: int
    competitor_research_id: int
    canonical_url: HttpUrl
    source_type: str | None
    discovery_method: str | None
    status: str
    attempt_count: int
    last_http_status: int | None
    last_attempted_at: datetime | None
    failure_category: str | None
    failure_reason: str | None
    content_hash: str | None
    created_at: datetime
    updated_at: datetime
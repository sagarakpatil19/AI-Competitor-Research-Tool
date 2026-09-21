from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class CompetitorEvidenceCreate(BaseModel):
    source_url: HttpUrl
    source_title: str | None = Field(default=None, max_length=500)
    source_type: str | None = Field(default=None, max_length=100)
    publisher: str | None = Field(default=None, max_length=255)
    published_at: datetime | None = None
    retrieved_at: datetime | None = None
    content: str | None = None
    content_excerpt: str | None = None


class CompetitorEvidenceResponse(BaseModel):
    id: int
    competitor_research_id: int
    source_id: int | None
    source_url: HttpUrl
    source_title: str | None
    source_type: str | None
    publisher: str | None
    published_at: datetime | None
    retrieved_at: datetime | None
    content: str | None
    content_excerpt: str | None
    processing_status: str
    validation_status: str
    processing_error: str | None
    validation_reason: str | None
    normalized_content: str | None
    normalized_excerpt: str | None
    normalized_content_hash: str | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime
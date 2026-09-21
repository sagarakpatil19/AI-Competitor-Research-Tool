from datetime import datetime

from pydantic import BaseModel, Field


class CompetitorResearchFactEvidenceCreate(BaseModel):
    fact_id: int
    evidence_id: int
    citation_excerpt: str | None = Field(default=None, max_length=10000)


class CompetitorResearchFactEvidenceResponse(CompetitorResearchFactEvidenceCreate):
    created_at: datetime

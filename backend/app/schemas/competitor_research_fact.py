from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CompetitorResearchFactCreate(BaseModel):
    section: str = Field(min_length=1, max_length=32)
    fact_type: str = Field(min_length=1, max_length=100)
    subject: str | None = Field(default=None, max_length=500)
    value_text: str | None = None
    value_numeric: Decimal | None = None
    currency: str | None = Field(default=None, max_length=3)
    unit: str | None = Field(default=None, max_length=100)
    period: str | None = Field(default=None, max_length=100)
    normalized_key: str = Field(min_length=1, max_length=1024)


class CompetitorResearchFactResponse(CompetitorResearchFactCreate):
    id: int
    competitor_research_id: int
    created_at: datetime
    updated_at: datetime

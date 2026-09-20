from datetime import datetime

from pydantic import BaseModel, Field


class CompetitorResearchUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=10000)
    industry: str | None = Field(default=None, max_length=255)
    products_services: str | None = Field(default=None, max_length=10000)
    target_customers: str | None = Field(default=None, max_length=10000)
    business_model: str | None = Field(default=None, max_length=10000)


class CompetitorResearchResponse(BaseModel):
    id: int
    competitor_id: int
    description: str | None
    industry: str | None
    products_services: str | None
    target_customers: str | None
    business_model: str | None
    created_at: datetime
    updated_at: datetime
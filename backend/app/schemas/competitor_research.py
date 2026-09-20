from datetime import datetime

from pydantic import BaseModel


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
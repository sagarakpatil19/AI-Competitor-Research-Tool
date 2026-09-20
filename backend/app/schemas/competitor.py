from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class CompetitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    description: str | None = None


class CompetitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    description: str | None = None


class CompetitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int | None
    research_run_id: int | None
    name: str
    domain: str | None
    website: AnyHttpUrl | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class DiscoveryCandidate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1, max_length=255)


class DiscoveryRequest(BaseModel):
    competitors: list[DiscoveryCandidate] = Field(min_length=1)


class DiscoveredCompetitorResponse(BaseModel):
    id: int
    research_run_id: int
    name: str
    domain: str
    created_at: datetime
    updated_at: datetime

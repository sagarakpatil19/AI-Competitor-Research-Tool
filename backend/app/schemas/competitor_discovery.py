from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


DiscoveryRunStatus = Literal["pending", "running", "completed", "failed", "no_candidates"]
DiscoveryStatus = Literal["received", "normalized", "duplicate", "failed"]
ValidationStatus = Literal["pending", "valid", "invalid", "same_company", "rejected", "promoted"]


class CompetitorDiscoveryRunCreate(BaseModel):
    research_run_id: int
    provider_name: str = Field(min_length=1, max_length=100)


class CompetitorDiscoveryRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    research_run_id: int
    provider_name: str
    status: DiscoveryRunStatus
    failure_category: str | None
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CompetitorDiscoveryCandidateCreate(BaseModel):
    discovery_run_id: int
    research_run_id: int
    candidate_name: str = Field(min_length=1, max_length=255)
    normalized_name: str = Field(min_length=1, max_length=255)
    domain: str | None = Field(default=None, max_length=255)
    canonical_url: AnyHttpUrl | None = None
    discovery_method: str = Field(min_length=1, max_length=100)
    provider_name: str = Field(min_length=1, max_length=100)
    provider_candidate_id: str | None = Field(default=None, max_length=255)
    provider_rank: int | None = Field(default=None, ge=1)
    discovery_status: DiscoveryStatus = "received"
    validation_status: ValidationStatus = "pending"
    validation_reason: str | None = None
    competitor_id: int | None = None


class CompetitorDiscoveryCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    discovery_run_id: int
    research_run_id: int
    candidate_name: str
    normalized_name: str
    domain: str | None
    canonical_url: AnyHttpUrl | None
    discovery_method: str
    provider_name: str
    provider_candidate_id: str | None
    provider_rank: int | None
    discovery_status: DiscoveryStatus
    validation_status: ValidationStatus
    validation_reason: str | None
    competitor_id: int | None
    created_at: datetime
    updated_at: datetime


class CompetitorDiscoveryCandidateSourceCreate(BaseModel):
    candidate_id: int
    source_url: AnyHttpUrl
    canonical_url: AnyHttpUrl
    source_title: str | None = Field(default=None, max_length=500)
    source_snippet: str | None = None
    provider_name: str = Field(min_length=1, max_length=100)
    provider_result_id: str | None = Field(default=None, max_length=255)
    provider_rank: int | None = Field(default=None, ge=1)


class CompetitorDiscoveryCandidateSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    source_url: AnyHttpUrl
    canonical_url: AnyHttpUrl
    source_title: str | None
    source_snippet: str | None
    provider_name: str
    provider_result_id: str | None
    provider_rank: int | None
    created_at: datetime

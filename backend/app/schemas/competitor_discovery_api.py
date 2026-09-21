from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict


class DiscoveryRunApiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    research_run_id: int
    provider_name: str
    status: Literal["pending", "running", "completed", "failed", "no_candidates"]
    failure_category: str | None
    failure_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DiscoveryCandidateSourceApiResponse(BaseModel):
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


class DiscoveryCandidateApiResponse(BaseModel):
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
    discovery_status: Literal["received", "normalized", "duplicate", "failed"]
    validation_status: Literal["pending", "valid", "invalid", "same_company", "rejected", "promoted"]
    validation_reason: str | None
    competitor_id: int | None
    created_at: datetime
    updated_at: datetime
    sources: list[DiscoveryCandidateSourceApiResponse]


class CompetitorDiscoveryApiResponse(BaseModel):
    research_run: DiscoveryRunApiResponse
    candidates: list[DiscoveryCandidateApiResponse]

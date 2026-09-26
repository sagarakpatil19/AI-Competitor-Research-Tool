from typing import Any, Literal

from pydantic import BaseModel, Field


class AIAnalysisRequest(BaseModel):
    scope: Literal["competitor", "research_run"]
    competitor_research_id: int | None = Field(default=None, gt=0)
    competitor_research_ids: list[int] | None = None
    contract_version: str = Field(default="contract-v1", min_length=1, max_length=100)
    prompt_version: str = Field(default="prompt-v1", min_length=1, max_length=100)


class BackgroundOperationResponse(BaseModel):
    logical_id: str
    research_run_id: int
    operation: str
    status: Literal["queued", "running", "retrying", "completed", "failed"]
    attempt_count: int
    max_attempts: int
    resource_reference: dict[str, Any]
    result: dict[str, Any] | list[Any] | None = None
    failure_category: str | None = None
    failure_reason: str | None = None
    status_url: str
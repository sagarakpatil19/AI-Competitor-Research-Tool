from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


AnalysisScope = Literal["competitor", "research_run"]


class AnalysisContextRequest(BaseModel):
    scope: AnalysisScope
    research_run_id: int = Field(gt=0)
    competitor_research_id: int | None = Field(default=None, gt=0)
    competitor_research_ids: list[int] = Field(default_factory=list)
    contract_version: str = Field(min_length=1, max_length=100)
    prompt_version: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_scope_selection(self) -> "AnalysisContextRequest":
        if any(execution_id <= 0 for execution_id in self.competitor_research_ids):
            raise ValueError("Competitor research execution IDs must be positive")
        if len(self.competitor_research_ids) != len(set(self.competitor_research_ids)):
            raise ValueError("Duplicate competitor research execution IDs are not allowed")
        if self.scope == "competitor":
            if self.competitor_research_id is None:
                raise ValueError("Competitor scope requires competitor_research_id")
            if self.competitor_research_ids:
                raise ValueError("Competitor scope does not accept competitor_research_ids")
        elif self.competitor_research_id is not None:
            raise ValueError("Research-run scope does not accept competitor_research_id")
        elif not self.competitor_research_ids:
            raise ValueError("Research-run scope requires explicit competitor_research_ids")
        return self


class ContextCompetitor(BaseModel):
    context_id: str
    name: str
    domain: str | None
    website: str | None
    research_execution_status: str


class ContextFact(BaseModel):
    context_id: str
    competitor_context_id: str
    section: str
    fact_type: str
    subject: str | None
    value_text: str | None
    value_numeric: Decimal | None
    currency: str | None
    unit: str | None
    period: str | None
    normalized_key: str
    evidence_context_ids: list[str]


class ContextEvidence(BaseModel):
    context_id: str
    competitor_context_id: str
    content: str
    normalized_excerpt: str | None
    content_hash: str | None
    processing_status: str
    validation_status: str
    source_context_id: str | None
    source_url: str
    source_title: str | None
    source_type: str | None
    publisher: str | None
    published_at: datetime | None
    retrieved_at: datetime | None
    fact_context_ids: list[str]


class ContextSource(BaseModel):
    context_id: str
    canonical_url: str
    source_type: str | None
    discovery_method: str | None
    status: str
    last_http_status: int | None
    last_attempted_at: datetime | None
    content_hash: str | None
    domain: str | None


class ContextSection(BaseModel):
    competitor_context_id: str
    section: str
    status: str
    reason: str | None
    fact_count: int
    valid_evidence_count: int
    evidence_without_fact_count: int


class ContextMapping(BaseModel):
    competitor_context_to_database_id: dict[str, int]
    competitor_context_to_competitor_id: dict[str, int]
    fact_context_to_database_id: dict[str, int]
    evidence_context_to_database_id: dict[str, int]
    source_context_to_database_id: dict[str, int]
    database_competitor_to_context_id: dict[int, str]
    database_fact_to_context_id: dict[int, str]
    database_evidence_to_context_id: dict[int, str]
    database_source_to_context_id: dict[int, str]


class SnapshotMetadata(BaseModel):
    algorithm: Literal["sha256"] = "sha256"
    input_snapshot_hash: str
    canonicalization_version: str
    contract_version: str
    prompt_version: str
    generated_at: datetime


class AnalysisContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: str
    prompt_version: str
    scope: AnalysisScope
    competitors: list[ContextCompetitor]
    sections: list[ContextSection]
    facts: list[ContextFact]
    evidence: list[ContextEvidence]
    sources: list[ContextSource]
    snapshot: SnapshotMetadata


class InternalContextResult(BaseModel):
    context: AnalysisContext
    mapping: ContextMapping

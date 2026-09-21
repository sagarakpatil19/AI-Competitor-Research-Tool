from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.context.analysis_context import AnalysisContext
from app.ai.errors import ProviderInvalidOutputError


StatementType = Literal["observation", "feedback_insight", "conflict", "evidence_gap"]
SupportStatus = Literal["supported", "partially_supported", "conflicting", "insufficient_evidence"]
FactReferenceRole = Literal["supports", "contradicts", "context"]
EvidenceReferenceRole = Literal["supports", "contradicts", "quotes", "context"]
ComparisonRole = Literal["subject", "baseline", "compared"]


class AIStatementResult(BaseModel):
    statement_id: str = Field(min_length=1)
    statement_type: StatementType
    text: str = Field(min_length=1)
    support_status: SupportStatus
    competitor_context_id: str | None = None
    fact_context_ids: list[str] = Field(default_factory=list)
    evidence_context_ids: list[str] = Field(default_factory=list)
    source_context_ids: list[str] = Field(default_factory=list)
    fact_roles: dict[str, FactReferenceRole] = Field(default_factory=dict)
    evidence_roles: dict[str, EvidenceReferenceRole] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_role_keys(self) -> "AIStatementResult":
        if set(self.fact_roles) - set(self.fact_context_ids):
            raise ValueError("Fact roles contain an unreferenced context ID")
        if set(self.evidence_roles) - set(self.evidence_context_ids):
            raise ValueError("Evidence roles contain an unreferenced context ID")
        return self


class AIComparisonResult(BaseModel):
    comparison_id: str = Field(min_length=1)
    comparison_type: str = Field(min_length=1, max_length=32)
    dimension: str = Field(min_length=1, max_length=100)
    statement: str = Field(min_length=1)
    support_status: SupportStatus
    competitor_context_ids: list[str] = Field(min_length=2)
    fact_context_ids: list[str] = Field(default_factory=list)
    evidence_context_ids: list[str] = Field(default_factory=list)
    source_context_ids: list[str] = Field(default_factory=list)
    competitor_roles: dict[str, ComparisonRole] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_roles(self) -> "AIComparisonResult":
        if set(self.competitor_roles) - set(self.competitor_context_ids):
            raise ValueError("Comparison roles contain an unreferenced context ID")
        return self


class ProviderAnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    scope: Literal["competitor", "research_run"]
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=255)
    statements: list[AIStatementResult] = Field(default_factory=list)
    comparisons: list[AIComparisonResult] = Field(default_factory=list)


def validate_provider_result(
    context: AnalysisContext,
    result: ProviderAnalysisResult,
) -> ProviderAnalysisResult:
    if result.scope != context.scope:
        raise ProviderInvalidOutputError("Provider result scope does not match analysis context")

    competitors = {item.context_id: item for item in context.competitors}
    facts = {item.context_id: item for item in context.facts}
    evidence = {item.context_id: item for item in context.evidence}
    sources = {item.context_id: item for item in context.sources}

    def require_ids(ids: list[str], available: dict[str, object], kind: str) -> None:
        unknown = sorted(set(ids) - set(available))
        if unknown:
            raise ProviderInvalidOutputError(f"Unknown {kind} context ID: {unknown[0]}")
        if len(ids) != len(set(ids)):
            raise ProviderInvalidOutputError(f"Duplicate {kind} context IDs are not allowed")

    for statement in result.statements:
        require_ids(statement.fact_context_ids, facts, "fact")
        require_ids(statement.evidence_context_ids, evidence, "evidence")
        require_ids(statement.source_context_ids, sources, "source")
        if statement.competitor_context_id is not None:
            require_ids([statement.competitor_context_id], competitors, "competitor")
        for fact_id in statement.fact_context_ids:
            fact = facts[fact_id]
            if statement.competitor_context_id and fact.competitor_context_id != statement.competitor_context_id:
                raise ProviderInvalidOutputError("Statement fact belongs to another competitor context")
        for evidence_id in statement.evidence_context_ids:
            item = evidence[evidence_id]
            if statement.competitor_context_id and item.competitor_context_id != statement.competitor_context_id:
                raise ProviderInvalidOutputError("Statement evidence belongs to another competitor context")
            if item.source_context_id and item.source_context_id not in statement.source_context_ids:
                raise ProviderInvalidOutputError("Statement evidence source is not referenced")

    for comparison in result.comparisons:
        if result.scope != "research_run":
            raise ProviderInvalidOutputError("Comparisons require research_run scope")
        require_ids(comparison.competitor_context_ids, competitors, "competitor")
        require_ids(comparison.fact_context_ids, facts, "fact")
        require_ids(comparison.evidence_context_ids, evidence, "evidence")
        require_ids(comparison.source_context_ids, sources, "source")
        for fact_id in comparison.fact_context_ids:
            if facts[fact_id].competitor_context_id not in comparison.competitor_context_ids:
                raise ProviderInvalidOutputError("Comparison fact is outside comparison competitors")
        for evidence_id in comparison.evidence_context_ids:
            if evidence[evidence_id].competitor_context_id not in comparison.competitor_context_ids:
                raise ProviderInvalidOutputError("Comparison evidence is outside comparison competitors")

    return result

import pytest
from pydantic import ValidationError

from app.ai.contracts import (
    AIComparisonResult,
    AIStatementResult,
    ProviderAnalysisResult,
    validate_provider_result,
)
from app.ai.errors import (
    AIProviderError,
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.context.analysis_context import (
    AnalysisContext,
    ContextCompetitor,
    ContextEvidence,
    ContextFact,
    ContextSection,
    ContextSource,
    SnapshotMetadata,
)
from app.ai.provider import AIProvider


def make_context(scope: str = "competitor") -> AnalysisContext:
    competitor = ContextCompetitor(
        context_id="COMPETITOR_001",
        name="Acme",
        domain="acme.example",
        website=None,
        research_execution_status="completed",
    )
    fact = ContextFact(
        context_id="FACT_001",
        competitor_context_id="COMPETITOR_001",
        section="pricing",
        fact_type="starting_price",
        subject=None,
        value_text=None,
        value_numeric=29,
        currency="USD",
        unit="month",
        period=None,
        normalized_key="pricing:starting_price:month",
        evidence_context_ids=["EVIDENCE_001"],
    )
    evidence = ContextEvidence(
        context_id="EVIDENCE_001",
        competitor_context_id="COMPETITOR_001",
        content="Plans start at $29 per month.",
        normalized_excerpt="Plans start at $29 per month.",
        content_hash="a" * 64,
        processing_status="processed",
        validation_status="valid",
        source_context_id="SOURCE_001",
        source_url="https://acme.example/pricing",
        source_title="Pricing",
        source_type="pricing",
        publisher=None,
        published_at=None,
        retrieved_at=None,
        fact_context_ids=["FACT_001"],
    )
    competitors = [competitor]
    facts = [fact]
    evidence_items = [evidence]
    sources = [
        ContextSource(
            context_id="SOURCE_001",
            canonical_url="https://acme.example/pricing",
            source_type="pricing",
            discovery_method="manual",
            status="collected",
            last_http_status=200,
            last_attempted_at=None,
            content_hash="a" * 64,
            domain="acme.example",
        )
    ]
    sections = [
        ContextSection(
            competitor_context_id="COMPETITOR_001",
            section="pricing",
            status="structured",
            reason=None,
            fact_count=1,
            valid_evidence_count=1,
            evidence_without_fact_count=0,
        )
    ]
    if scope == "research_run":
        competitors.append(competitor.model_copy(update={
            "context_id": "COMPETITOR_002",
            "name": "Beta",
            "domain": "beta.example",
        }))
        facts.append(fact.model_copy(update={
            "context_id": "FACT_002",
            "competitor_context_id": "COMPETITOR_002",
            "value_numeric": 49,
            "normalized_key": "pricing:starting_price:month:beta",
            "evidence_context_ids": ["EVIDENCE_002"],
        }))
        evidence_items.append(evidence.model_copy(update={
            "context_id": "EVIDENCE_002",
            "competitor_context_id": "COMPETITOR_002",
            "content": "Plans start at $49 per month.",
            "normalized_excerpt": "Plans start at $49 per month.",
            "content_hash": "b" * 64,
            "source_context_id": "SOURCE_002",
            "source_url": "https://beta.example/pricing",
            "fact_context_ids": ["FACT_002"],
        }))
        sources.append(sources[0].model_copy(update={
            "context_id": "SOURCE_002",
            "canonical_url": "https://beta.example/pricing",
            "domain": "beta.example",
            "content_hash": "b" * 64,
        }))
        sections.append(sections[0].model_copy(update={
            "competitor_context_id": "COMPETITOR_002",
        }))

    return AnalysisContext(
        contract_version="contract-v1",
        prompt_version="prompt-v1",
        scope=scope,
        competitors=competitors,
        sections=sections,
        facts=facts,
        evidence=evidence_items,
        sources=sources,
        snapshot=SnapshotMetadata(
            input_snapshot_hash="b" * 64,
            canonicalization_version="m12-context-v1",
            contract_version="contract-v1",
            prompt_version="prompt-v1",
            generated_at="2026-09-22T00:00:00Z",
        ),
    )


def valid_result(scope: str = "competitor") -> ProviderAnalysisResult:
    return ProviderAnalysisResult(
        scope=scope,
        provider="fake-provider",
        model="fake-model",
        statements=[
            AIStatementResult(
                statement_id="STATEMENT_001",
                statement_type="observation",
                text="The listed starting price is $29 per month.",
                support_status="supported",
                competitor_context_id="COMPETITOR_001",
                fact_context_ids=["FACT_001"],
                evidence_context_ids=["EVIDENCE_001"],
                source_context_ids=["SOURCE_001"],
                fact_roles={"FACT_001": "supports"},
                evidence_roles={"EVIDENCE_001": "quotes"},
            )
        ],
    )


def test_fake_provider_implements_ai_provider_contract():
    class FakeProvider:
        def analyze(self, context: AnalysisContext) -> ProviderAnalysisResult:
            return valid_result(context.scope)

    provider: AIProvider = FakeProvider()
    result = provider.analyze(make_context())
    assert result.provider == "fake-provider"
    assert result.statements[0].fact_context_ids == ["FACT_001"]


def test_valid_references_are_accepted_for_competitor_scope():
    result = validate_provider_result(make_context(), valid_result())
    assert result.statements[0].evidence_context_ids == ["EVIDENCE_001"]


def test_research_run_scope_can_represent_comparisons():
    context = make_context("research_run")
    result = ProviderAnalysisResult(
        scope="research_run",
        provider="fake-provider",
        model="fake-model",
        comparisons=[
            AIComparisonResult(
                comparison_id="COMPARISON_001",
                comparison_type="pricing",
                dimension="starting_price",
                statement="The selected executions can be compared on starting price.",
                support_status="supported",
                competitor_context_ids=["COMPETITOR_001", "COMPETITOR_002"],
                fact_context_ids=["FACT_001"],
                evidence_context_ids=["EVIDENCE_001"],
                source_context_ids=["SOURCE_001"],
            )
        ],
    )
    validated = validate_provider_result(context, result)
    assert validated.comparisons[0].competitor_context_ids == ["COMPETITOR_001", "COMPETITOR_002"]


def test_duplicate_references_are_rejected():
    context = make_context()
    for field, value, message in (
        ("fact_context_ids", ["FACT_001", "FACT_001"], "fact"),
        ("evidence_context_ids", ["EVIDENCE_001", "EVIDENCE_001"], "evidence"),
        ("source_context_ids", ["SOURCE_001", "SOURCE_001"], "source"),
    ):
        statement = AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="observation",
            text="Duplicate reference.",
            support_status="supported",
            competitor_context_id="COMPETITOR_001",
            fact_context_ids=["FACT_001"],
            evidence_context_ids=["EVIDENCE_001"],
            source_context_ids=["SOURCE_001"],
            fact_roles={"FACT_001": "supports"},
            evidence_roles={"EVIDENCE_001": "quotes"},
        ).model_copy(update={field: value})
        with pytest.raises(ProviderInvalidOutputError, match=message):
            validate_provider_result(context, ProviderAnalysisResult(
                scope="competitor", provider="fake-provider", model="fake-model", statements=[statement]
            ))

    comparison = AIComparisonResult(
        comparison_id="COMPARISON_001",
        comparison_type="pricing",
        dimension="starting_price",
        statement="Duplicate competitor reference.",
        support_status="supported",
        competitor_context_ids=["COMPETITOR_001", "COMPETITOR_001"],
    )
    with pytest.raises(ProviderInvalidOutputError, match="competitor"):
        validate_provider_result(
            make_context("research_run"),
            ProviderAnalysisResult(
                scope="research_run", provider="fake-provider", model="fake-model", comparisons=[comparison]
            ),
        )


def test_comparison_is_rejected_for_competitor_scope():
    comparison = AIComparisonResult(
        comparison_id="COMPARISON_001",
        comparison_type="pricing",
        dimension="starting_price",
        statement="Comparison is not valid for competitor scope.",
        support_status="supported",
        competitor_context_ids=["COMPETITOR_001", "COMPETITOR_002"],
    )
    with pytest.raises(ProviderInvalidOutputError, match="research_run scope"):
        validate_provider_result(
            make_context("competitor"),
            ProviderAnalysisResult(
                scope="competitor", provider="fake-provider", model="fake-model", comparisons=[comparison]
            ),
        )


def test_invalid_role_mappings_are_rejected():
    with pytest.raises(ValidationError, match="Fact roles"):
        AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="observation",
            text="Invalid fact role.",
            support_status="supported",
            fact_context_ids=["FACT_001"],
            fact_roles={"FACT_999": "supports"},
        )
    with pytest.raises(ValidationError, match="Evidence roles"):
        AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="observation",
            text="Invalid evidence role.",
            support_status="supported",
            evidence_context_ids=["EVIDENCE_001"],
            evidence_roles={"EVIDENCE_999": "supports"},
        )
    with pytest.raises(ValidationError, match="Comparison roles"):
        AIComparisonResult(
            comparison_id="COMPARISON_001",
            comparison_type="pricing",
            dimension="starting_price",
            statement="Invalid competitor role.",
            support_status="supported",
            competitor_context_ids=["COMPETITOR_001", "COMPETITOR_002"],
            competitor_roles={"COMPETITOR_999": "compared"},
        )


def test_unknown_reference_types_are_rejected():
    context = make_context()
    for field, value, message in (
        ("competitor_context_id", "COMPETITOR_999", "competitor"),
        ("fact_context_ids", ["FACT_999"], "fact"),
        ("evidence_context_ids", ["EVIDENCE_999"], "evidence"),
        ("source_context_ids", ["SOURCE_999"], "source"),
    ):
        statement = AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="observation",
            text="Unsupported reference.",
            support_status="supported",
            competitor_context_id="COMPETITOR_001",
            fact_context_ids=["FACT_001"],
            evidence_context_ids=["EVIDENCE_001"],
            source_context_ids=["SOURCE_001"],
            fact_roles={"FACT_001": "supports"},
            evidence_roles={"EVIDENCE_001": "supports"},
        )
        statement = statement.model_copy(update={field: value})
        if field == "fact_context_ids":
            statement = statement.model_copy(update={"fact_roles": {"FACT_999": "supports"}})
        if field == "evidence_context_ids":
            statement = statement.model_copy(update={"evidence_roles": {"EVIDENCE_999": "supports"}})
        with pytest.raises(ProviderInvalidOutputError, match=message):
            validate_provider_result(context, ProviderAnalysisResult(
                scope="competitor",
                provider="fake-provider",
                model="fake-model",
                statements=[statement],
            ))


def test_invalid_statement_values_are_rejected_by_contract():
    with pytest.raises(ValidationError):
        AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="unsupported",
            text="Invalid",
            support_status="supported",
        )
    with pytest.raises(ValidationError):
        AIStatementResult(
            statement_id="STATEMENT_001",
            statement_type="observation",
            text="Invalid",
            support_status="unsupported",
        )


def test_provider_error_hierarchy_is_provider_neutral():
    assert issubclass(ProviderUnavailableError, AIProviderError)
    assert issubclass(ProviderTimeoutError, AIProviderError)
    assert issubclass(ProviderResponseError, AIProviderError)
    assert issubclass(ProviderInvalidOutputError, AIProviderError)


def test_provider_contract_requires_context_ids_not_database_ids():
    statement = AIStatementResult(
        statement_id="STATEMENT_001",
        statement_type="evidence_gap",
        text="Evidence is insufficient.",
        support_status="insufficient_evidence",
    )
    serialized = statement.model_dump()
    assert "fact_id" not in serialized
    assert "evidence_id" not in serialized
    assert "competitor_research_id" not in serialized

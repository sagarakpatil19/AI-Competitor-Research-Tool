import pytest

from app.ai.contracts import AIComparisonResult, ProviderAnalysisResult
from app.ai.errors import (
    ProviderInvalidOutputError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.gemini_config import GeminiProviderConfig
from tests.test_ai_provider_contracts import make_context


class FakeResponse:
    def __init__(self, parsed=None, text=None):
        self.parsed = parsed
        self.text = text


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.models = FakeModels(response=response, error=error)


def valid_payload(scope="competitor"):
    return ProviderAnalysisResult(
        scope=scope,
        provider="gemini",
        model="gemini-3.8-flash",
        statements=[
            {
                "statement_id": "STATEMENT_001",
                "statement_type": "observation",
                "text": "The listed starting price is $29 per month.",
                "support_status": "supported",
                "competitor_context_id": "COMPETITOR_001",
                "fact_context_ids": ["FACT_001"],
                "evidence_context_ids": ["EVIDENCE_001"],
                "source_context_ids": ["SOURCE_001"],
                "fact_roles": {"FACT_001": "supports"},
                "evidence_roles": {"EVIDENCE_001": "quotes"},
            }
        ],
    )


def make_research_run_context():
    context = make_context("research_run")
    second_competitor = context.competitors[0].model_copy(update={
        "context_id": "COMPETITOR_002",
        "name": "Beta",
        "domain": "beta.example",
    })
    second_fact = context.facts[0].model_copy(update={
        "context_id": "FACT_002",
        "competitor_context_id": "COMPETITOR_002",
        "value_numeric": 49,
        "normalized_key": "pricing:starting_price:month:beta",
        "evidence_context_ids": ["EVIDENCE_002"],
    })
    second_evidence = context.evidence[0].model_copy(update={
        "context_id": "EVIDENCE_002",
        "competitor_context_id": "COMPETITOR_002",
        "content": "Plans start at $49 per month.",
        "normalized_excerpt": "Plans start at $49 per month.",
        "content_hash": "b" * 64,
        "source_context_id": "SOURCE_002",
        "source_url": "https://beta.example/pricing",
        "fact_context_ids": ["FACT_002"],
    })
    second_source = context.sources[0].model_copy(update={
        "context_id": "SOURCE_002",
        "canonical_url": "https://beta.example/pricing",
        "domain": "beta.example",
        "content_hash": "b" * 64,
    })
    second_section = context.sections[0].model_copy(update={
        "competitor_context_id": "COMPETITOR_002",
    })
    return context.model_copy(update={
        "competitors": [*context.competitors, second_competitor],
        "sections": [*context.sections, second_section],
        "facts": [*context.facts, second_fact],
        "evidence": [*context.evidence, second_evidence],
        "sources": [*context.sources, second_source],
    })


def test_valid_competitor_response_is_parsed_and_validated():
    client = FakeClient(response=FakeResponse(parsed=valid_payload().model_dump()))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key", model_name="gemini-3.8-flash"),
        client=client,
    )

    result = provider.analyze(make_context())

    assert result.provider == "gemini"
    assert result.statements[0].fact_context_ids == ["FACT_001"]


def test_valid_research_run_response_with_comparison_is_accepted():
    context = make_research_run_context()
    payload = valid_payload("research_run").model_copy(update={
        "statements": [],
        "comparisons": [AIComparisonResult(
            comparison_id="COMPARISON_001",
            comparison_type="pricing",
            dimension="starting_price",
            statement="The executions have different listed starting prices.",
            support_status="supported",
            competitor_context_ids=["COMPETITOR_001", "COMPETITOR_002"],
            fact_context_ids=["FACT_001", "FACT_002"],
            evidence_context_ids=["EVIDENCE_001", "EVIDENCE_002"],
            source_context_ids=["SOURCE_001", "SOURCE_002"],
        )],
    })
    client = FakeClient(response=FakeResponse(parsed=payload.model_dump()))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key", model_name="gemini-3.8-flash"),
        client=client,
    )

    result = provider.analyze(context)

    assert result.comparisons[0].competitor_context_ids == ["COMPETITOR_001", "COMPETITOR_002"]


def test_provider_uses_configured_model_and_semantic_context_ids():
    client = FakeClient(response=FakeResponse(parsed=valid_payload().model_dump()))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key", model_name="configured-model"),
        client=client,
    )

    provider.analyze(make_context())

    call = client.models.calls[0]
    assert call["model"] == "configured-model"
    instruction = call["contents"]
    assert "COMPETITOR_001" in instruction
    assert "FACT_001" in instruction
    assert "EVIDENCE_001" in instruction
    assert "SOURCE_001" in instruction
    assert "competitor_research_id" not in instruction
    assert "research_run_id" not in instruction
    assert call["config"].response_mime_type == "application/json"


def test_unknown_fact_evidence_and_competitor_references_are_rejected():
    for field, value, message in (
        ("fact_context_ids", ["FACT_999"], "Unknown fact"),
        ("evidence_context_ids", ["EVIDENCE_999"], "Unknown evidence"),
        ("competitor_context_id", "COMPETITOR_999", "Unknown competitor"),
    ):
        payload = valid_payload().model_dump()
        statement = payload["statements"][0]
        statement[field] = value
        if field == "fact_context_ids":
            statement["fact_roles"] = {"FACT_999": "supports"}
        if field == "evidence_context_ids":
            statement["evidence_roles"] = {"EVIDENCE_999": "quotes"}
        client = FakeClient(response=FakeResponse(parsed=payload))
        provider = GeminiProvider(config=GeminiProviderConfig(api_key="test-key"), client=client)
        with pytest.raises(ProviderInvalidOutputError, match=message):
            provider.analyze(make_context())


def test_invalid_structured_response_is_rejected():
    client = FakeClient(response=FakeResponse(text="not-json"))
    provider = GeminiProvider(config=GeminiProviderConfig(api_key="test-key"), client=client)

    with pytest.raises(ProviderInvalidOutputError, match="invalid structured output"):
        provider.analyze(make_context())


def test_timeout_and_provider_failures_are_mapped():
    class FakeTimeoutError(Exception):
        pass

    timeout_provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key"),
        client=FakeClient(error=FakeTimeoutError("timeout")),
    )
    with pytest.raises(ProviderTimeoutError):
        timeout_provider.analyze(make_context())

    class FakeAuthenticationError(Exception):
        pass

    auth_provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key"),
        client=FakeClient(error=FakeAuthenticationError("authentication failed with secret")),
    )
    with pytest.raises(ProviderUnavailableError) as error:
        auth_provider.analyze(make_context())
    assert "secret" not in str(error.value)

    response_provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key"),
        client=FakeClient(error=RuntimeError("transport failure")),
    )
    with pytest.raises(ProviderResponseError):
        response_provider.analyze(make_context())


def test_missing_api_key_is_handled_without_network_access():
    provider = GeminiProvider(config=GeminiProviderConfig(api_key=None))

    with pytest.raises(ProviderUnavailableError, match="GEMINI_API_KEY"):
        provider.analyze(make_context())


def test_api_key_is_not_in_provider_repr_or_errors():
    secret = "test-secret-key"
    provider = GeminiProvider(config=GeminiProviderConfig(api_key=secret), client=FakeClient(error=RuntimeError("failed")))

    assert secret not in repr(provider.config)
    with pytest.raises(ProviderResponseError) as error:
        provider.analyze(make_context())
    assert secret not in str(error.value)

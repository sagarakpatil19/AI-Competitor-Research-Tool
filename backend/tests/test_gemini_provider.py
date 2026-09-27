import json

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


def wire_payload(result):
    payload = result.model_dump()
    for statement in payload["statements"]:
        statement["fact_roles"] = [
            {"context_id": context_id, "role": role}
            for context_id, role in statement["fact_roles"].items()
        ]
        statement["evidence_roles"] = [
            {"context_id": context_id, "role": role}
            for context_id, role in statement["evidence_roles"].items()
        ]
    for comparison in payload["comparisons"]:
        comparison["competitor_roles"] = [
            {"context_id": context_id, "role": role}
            for context_id, role in comparison["competitor_roles"].items()
        ]
    return payload


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
    client = FakeClient(response=FakeResponse(parsed=wire_payload(valid_payload())))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key", model_name="gemini-3.8-flash"),
        client=client,
    )

    result = provider.analyze(make_context())

    assert result.provider == "gemini"
    assert result.statements[0].fact_context_ids == ["FACT_001"]
    assert result.statements[0].fact_roles == {"FACT_001": "supports"}
    assert result.statements[0].evidence_roles == {"EVIDENCE_001": "quotes"}


def test_valid_wire_json_text_fallback_is_parsed():
    client = FakeClient(response=FakeResponse(text=json.dumps(wire_payload(valid_payload()))))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key"),
        client=client,
    )

    result = provider.analyze(make_context())

    assert result.statements[0].fact_roles == {"FACT_001": "supports"}
    assert result.statements[0].evidence_roles == {"EVIDENCE_001": "quotes"}


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
            competitor_roles={"COMPETITOR_001": "subject", "COMPETITOR_002": "compared"},
        )],
    })
    client = FakeClient(response=FakeResponse(parsed=wire_payload(payload)))
    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key", model_name="gemini-3.8-flash"),
        client=client,
    )

    result = provider.analyze(context)

    assert result.comparisons[0].competitor_context_ids == ["COMPETITOR_001", "COMPETITOR_002"]
    assert result.comparisons[0].competitor_roles == {
        "COMPETITOR_001": "subject",
        "COMPETITOR_002": "compared",
    }


def test_provider_uses_configured_model_and_semantic_context_ids():
    client = FakeClient(response=FakeResponse(parsed=wire_payload(valid_payload())))
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


def test_response_config_uses_wire_schema_without_additional_properties():
    response_config = GeminiProvider._response_config()
    response_schema = response_config.response_schema
    schema = (
        response_schema.model_json_schema()
        if hasattr(response_schema, "model_json_schema")
        else response_schema
    )

    def assert_no_additional_properties(value):
        if isinstance(value, dict):
            assert "additionalProperties" not in value
            for child in value.values():
                assert_no_additional_properties(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_additional_properties(child)

    assert response_config.response_mime_type == "application/json"
    assert_no_additional_properties(schema)


def test_unknown_fact_evidence_and_competitor_references_are_rejected():
    for field, value, message in (
        ("fact_context_ids", ["FACT_999"], "Unknown fact"),
        ("evidence_context_ids", ["EVIDENCE_999"], "Unknown evidence"),
        ("competitor_context_id", "COMPETITOR_999", "Unknown competitor"),
    ):
        payload = wire_payload(valid_payload())
        statement = payload["statements"][0]
        statement[field] = value
        if field == "fact_context_ids":
            statement["fact_roles"] = [{"context_id": "FACT_999", "role": "supports"}]
        if field == "evidence_context_ids":
            statement["evidence_roles"] = [{"context_id": "EVIDENCE_999", "role": "quotes"}]
        client = FakeClient(response=FakeResponse(parsed=payload))
        provider = GeminiProvider(config=GeminiProviderConfig(api_key="test-key"), client=client)
        with pytest.raises(ProviderInvalidOutputError, match=message):
            provider.analyze(make_context())


@pytest.mark.parametrize(
    ("role_kind", "scope"),
    [("fact", "competitor"), ("evidence", "competitor"), ("competitor", "research_run")],
)
def test_duplicate_role_context_ids_are_rejected(role_kind, scope):
    payload = wire_payload(valid_payload(scope))
    if role_kind == "fact":
        payload["statements"][0]["fact_roles"] = [
            {"context_id": "FACT_001", "role": "supports"},
            {"context_id": "FACT_001", "role": "contradicts"},
        ]
    elif role_kind == "evidence":
        payload["statements"][0]["evidence_roles"] = [
            {"context_id": "EVIDENCE_001", "role": "quotes"},
            {"context_id": "EVIDENCE_001", "role": "supports"},
        ]
    else:
        payload["statements"] = []
        payload["comparisons"] = [{
            "comparison_id": "COMPARISON_001",
            "comparison_type": "pricing",
            "dimension": "starting_price",
            "statement": "The listed starting prices differ.",
            "support_status": "supported",
            "competitor_context_ids": ["COMPETITOR_001", "COMPETITOR_002"],
            "fact_context_ids": [],
            "evidence_context_ids": [],
            "source_context_ids": [],
            "competitor_roles": [
                {"context_id": "COMPETITOR_001", "role": "subject"},
                {"context_id": "COMPETITOR_001", "role": "compared"},
            ],
        }]

    provider = GeminiProvider(
        config=GeminiProviderConfig(api_key="test-key"),
        client=FakeClient(response=FakeResponse(parsed=payload)),
    )
    context = make_research_run_context() if scope == "research_run" else make_context()

    with pytest.raises(ProviderInvalidOutputError, match=f"duplicate {role_kind} role context ID"):
        provider.analyze(context)


def test_invalid_structured_response_is_rejected():
    client = FakeClient(response=FakeResponse(text="not-json"))
    provider = GeminiProvider(config=GeminiProviderConfig(api_key="test-key"), client=client)

    with pytest.raises(ProviderInvalidOutputError, match="invalid structured output"):
        provider.analyze(make_context())


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(text="   "),
        FakeResponse(text=None),
        FakeResponse(parsed=None, text=None),
        FakeResponse(parsed={"scope": "competitor", "model": "m"}, text='{"scope": "competitor", "model": "m"}'),
        FakeResponse(parsed={"scope": "competitor", "provider": "gemini"}, text='{"scope": "competitor", "provider": "gemini"}'),
        FakeResponse(parsed={"provider": "gemini", "model": "m"}, text='{"provider": "gemini", "model": "m"}'),
    ],
)
def test_empty_or_invalid_structured_payloads_are_rejected(response):
    client = FakeClient(response=response)
    provider = GeminiProvider(config=GeminiProviderConfig(api_key="test-key"), client=client)

    with pytest.raises(ProviderInvalidOutputError):
        provider.analyze(make_context())


def test_provider_error_messages_do_not_expose_the_api_key():
    secret = "super-secret-key"
    client = FakeClient(error=RuntimeError(f"API key {secret} rejected by Gemini"))
    provider = GeminiProvider(config=GeminiProviderConfig(api_key=secret), client=client)

    with pytest.raises(ProviderUnavailableError) as error:
        provider.analyze(make_context())

    assert secret not in str(error.value)


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

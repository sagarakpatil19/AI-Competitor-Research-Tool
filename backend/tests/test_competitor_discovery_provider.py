import httpx
import pytest

from app.integrations.competitor_discovery_base import DiscoveryCompanyContext
from app.integrations.competitor_discovery_base import (
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderResponseError,
    DiscoveryProviderTimeoutError,
)
from app.integrations.competitor_discovery_queries import build_discovery_queries
from app.integrations.tavily_competitor_discovery import TavilyCompetitorDiscoveryProvider


def test_query_builder_uses_company_name_and_optional_industry():
    queries = build_discovery_queries(
        DiscoveryCompanyContext(
            company_name="  Acme  ",
            domain="acme.example",
            industry="  Productivity software ",
            description=None,
        )
    )

    assert [query.query for query in queries] == [
        "Acme competitors",
        "Acme alternatives",
        "companies similar to Acme",
        "Productivity software companies similar to Acme",
    ]
    assert [query.discovery_method for query in queries] == [
        "search_competitors",
        "search_alternatives",
        "search_similar_companies",
        "search_industry_similar",
    ]


def test_query_builder_falls_back_to_domain_and_never_emits_empty_queries():
    queries = build_discovery_queries(
        DiscoveryCompanyContext(
            company_name=None,
            domain=" acme.example ",
            industry=" ",
            description=None,
        )
    )

    assert queries
    assert all(query.query for query in queries)
    assert queries[0].query == "acme.example competitors"


def test_query_builder_deduplicates_deterministically():
    queries = build_discovery_queries(
        DiscoveryCompanyContext(
            company_name="Acme",
            domain=None,
            industry="Acme",
            description=None,
        )
    )

    assert len(queries) == len({query.query.casefold() for query in queries})


def make_provider(handler, api_key="test-key"):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return TavilyCompetitorDiscoveryProvider(api_key=api_key, client=client), client


def test_tavily_provider_parses_results_and_request_configuration():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "url": "https://www.slack.com/pricing#plans",
                        "title": "Slack pricing",
                        "content": "Team collaboration platform",
                        "score": 0.9,
                    }
                ]
            },
        )

    provider, client = make_provider(handler)
    try:
        candidates = provider.discover(
            DiscoveryCompanyContext("Acme", None, None, None)
        )
    finally:
        client.close()

    assert len(requests) == 3
    request_payload = requests[0].read()
    assert b'"search_depth":"basic"' in request_payload
    assert b'"max_results":5' in request_payload
    assert b'"include_answer":false' in request_payload
    assert b'"include_raw_content":false' in request_payload
    assert requests[0].headers["authorization"] == "Bearer test-key"
    assert candidates[0].candidate_name is None
    assert candidates[0].candidate_domain == "slack.com"
    assert candidates[0].source_title == "Slack pricing"
    assert candidates[0].source_snippet == "Team collaboration platform"
    assert candidates[0].provider_name == "tavily"
    assert candidates[0].provider_rank == 1
    assert candidates[0].discovery_method == "search_competitors"


def test_tavily_provider_preserves_method_for_each_query():
    def handler(request):
        query = request.content.decode()
        if "alternatives" in query:
            url = "https://alternatives.example/result"
        elif "similar" in query:
            url = "https://similar.example/result"
        else:
            url = "https://competitors.example/result"
        return httpx.Response(200, json={"results": [{"url": url}]})

    provider, client = make_provider(handler)
    try:
        candidates = provider.discover(
            DiscoveryCompanyContext("Acme", None, None, None)
        )
    finally:
        client.close()

    assert [candidate.discovery_method for candidate in candidates] == [
        "search_competitors",
        "search_alternatives",
        "search_similar_companies",
    ]


def test_tavily_provider_skips_invalid_individual_results():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "results": [
                    {},
                    {"url": "ftp://invalid.example/result"},
                    {"url": "not a url"},
                    "not an object",
                    {"url": "https://valid.example/result"},
                ]
            },
        )

    provider, client = make_provider(handler)
    try:
        candidates = provider.discover(
            DiscoveryCompanyContext("Acme", None, None, None)
        )
    finally:
        client.close()

    assert [candidate.candidate_domain for candidate in candidates] == [
        "valid.example",
        "valid.example",
        "valid.example",
    ]
    assert all(candidate.provider_rank == 5 for candidate in candidates)


@pytest.mark.parametrize(
    ("status_code", "error_type"),
    [
        (401, DiscoveryProviderAuthenticationError),
        (403, DiscoveryProviderAuthenticationError),
        (429, DiscoveryProviderRateLimitError),
        (500, DiscoveryProviderResponseError),
        (503, DiscoveryProviderResponseError),
    ],
)
def test_tavily_provider_maps_http_failures(status_code, error_type):
    provider, client = make_provider(lambda request: httpx.Response(status_code))
    try:
        with pytest.raises(error_type):
            provider.discover(DiscoveryCompanyContext("Acme", None, None, None))
    finally:
        client.close()


def test_tavily_provider_maps_timeout_and_connection_failures():
    def timeout_handler(request):
        raise httpx.ReadTimeout("timeout")

    provider, client = make_provider(timeout_handler)
    try:
        with pytest.raises(DiscoveryProviderTimeoutError):
            provider.discover(DiscoveryCompanyContext("Acme", None, None, None))
    finally:
        client.close()

    def connection_handler(request):
        raise httpx.ConnectError("connection details")

    provider, client = make_provider(connection_handler)
    try:
        with pytest.raises(DiscoveryProviderResponseError):
            provider.discover(DiscoveryCompanyContext("Acme", None, None, None))
    finally:
        client.close()


def test_tavily_provider_rejects_malformed_top_level_response():
    provider, client = make_provider(lambda request: httpx.Response(200, json={"answer": "ignored"}))
    try:
        with pytest.raises(DiscoveryProviderResponseError):
            provider.discover(DiscoveryCompanyContext("Acme", None, None, None))
    finally:
        client.close()


def test_tavily_provider_does_not_expose_api_key_in_missing_key_error():
    provider, client = make_provider(lambda request: httpx.Response(200), api_key="")
    try:
        with pytest.raises(DiscoveryProviderAuthenticationError) as error:
            provider.discover(DiscoveryCompanyContext("Acme", None, None, None))
    finally:
        client.close()

    assert "Bearer" not in str(error.value)
    assert "test-key" not in str(error.value)

from app.integrations.competitor_discovery_base import (
    DiscoveryCompanyContext,
    RawDiscoveryCandidate,
)
from app.services.competitor_discovery import (
    DISCOVERY_FAILED,
    DISCOVERY_NORMALIZED,
    REASON_DUPLICATE_DOMAIN,
    REASON_INVALID_PROVENANCE_URL,
    REASON_INVALID_URL,
    REASON_SAME_COMPANY,
    VALIDATION_INVALID,
    VALIDATION_SAME_COMPANY,
    VALIDATION_VALID,
    normalize_candidate_name,
    normalize_domain,
    normalize_url,
    process_discovery_candidates,
)


def raw(url, name="Slack", result_url="https://news.example/result", **kwargs):
    return RawDiscoveryCandidate(
        candidate_name=name,
        candidate_url=url,
        candidate_domain=None,
        supporting_result_url=result_url,
        source_title=kwargs.get("source_title"),
        source_snippet=kwargs.get("source_snippet"),
        provider_name=kwargs.get("provider_name", "test-provider"),
        provider_result_id=kwargs.get("provider_result_id"),
        provider_rank=kwargs.get("provider_rank", 1),
        discovery_method=kwargs.get("discovery_method", "search_competitors"),
    )


def test_normalize_url_applies_conservative_url_rules():
    assert normalize_url("HTTPS://www.Example.com/") == ("https://example.com/", "example.com")
    assert normalize_url("https://www.example.com/pricing#plans") == (
        "https://example.com/pricing",
        "example.com",
    )
    assert normalize_url("http://example.com:80/") == ("http://example.com/", "example.com")
    assert normalize_url("https://example.com:443/features/") == (
        "https://example.com/features",
        "example.com",
    )


def test_normalize_url_rejects_invalid_inputs():
    for value in ("ftp://example.com", "https:///missing-host", "https://", "not a url"):
        try:
            normalize_url(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid URL: {value}")


def test_normalize_domain_is_shared_and_conservative():
    assert normalize_domain("  WWW.Example.COM. ") == "example.com"
    for value in (None, "", "www", "bad domain.example", "co.uk"):
        if value == "co.uk":
            assert normalize_domain(value) == "co.uk"
            continue
        try:
            normalize_domain(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid domain: {value}")


def test_normalize_name_collapses_whitespace_and_compares_case_insensitively():
    assert normalize_candidate_name("  Slack   Technologies  ") == (
        "Slack Technologies",
        "slack technologies",
    )
    assert normalize_candidate_name("SLACK") == ("SLACK", "slack")


def test_same_company_detects_domain_variants_and_paths():
    company = DiscoveryCompanyContext("Example", "example.com", None, None)
    results = process_discovery_candidates(
        company,
        [
            raw("https://www.Example.com/pricing", name="Other name"),
        ],
    )

    assert results[0].validation_status == VALIDATION_SAME_COMPANY
    assert results[0].validation_reason == REASON_SAME_COMPANY


def test_same_company_name_is_used_only_without_company_domain():
    company = DiscoveryCompanyContext("Example", None, None, None)
    result = process_discovery_candidates(company, [raw("https://example.com", name="  EXAMPLE ")])[0]

    assert result.validation_status == VALIDATION_SAME_COMPANY


def test_same_domain_deduplicates_paths_and_merges_all_provenance():
    company = DiscoveryCompanyContext("Acme", "acme.example", None, None)
    results = process_discovery_candidates(
        company,
        [
            raw("https://www.Slack.com/", result_url="https://news.example/second", source_title="Second"),
            raw("https://slack.com/pricing#plans", result_url="https://news.example/first", source_title="First"),
        ],
    )

    assert len(results) == 1
    assert results[0].domain == "slack.com"
    assert results[0].discovery_status == DISCOVERY_NORMALIZED
    assert results[0].validation_status == VALIDATION_VALID
    assert results[0].duplicate_count == 1
    assert [source.supporting_result_url for source in results[0].supporting_sources] == [
        "https://news.example/first",
        "https://news.example/second",
    ]


def test_different_domains_with_similar_names_remain_separate():
    results = process_discovery_candidates(
        DiscoveryCompanyContext("Acme", None, None, None),
        [raw("https://slack.com", name="Acme Labs"), raw("https://slacktools.example", name="Acme Labs")],
    )

    assert len(results) == 2
    assert {result.domain for result in results} == {"slack.com", "slacktools.example"}


def test_different_domains_with_same_name_remain_separate():
    result = process_discovery_candidates(
        DiscoveryCompanyContext("Acme", None, None, None),
        [raw("https://first.example", name="Same Name"), raw("https://second.example", name="Same Name")],
    )

    assert len(result) == 2


def test_malformed_candidate_and_provenance_receive_stable_failure_reasons():
    invalid_url = process_discovery_candidates(
        DiscoveryCompanyContext("Acme", None, None, None),
        [raw("ftp://invalid.example")],
    )[0]
    invalid_provenance = process_discovery_candidates(
        DiscoveryCompanyContext("Acme", None, None, None),
        [raw("https://valid.example", result_url="ftp://invalid.example")],
    )[0]

    assert invalid_url.discovery_status == DISCOVERY_FAILED
    assert invalid_url.validation_status == VALIDATION_INVALID
    assert invalid_url.validation_reason == REASON_INVALID_URL
    assert invalid_provenance.validation_reason == REASON_INVALID_PROVENANCE_URL


def test_processing_is_deterministic_for_same_input():
    company = DiscoveryCompanyContext("Acme", "acme.example", "SaaS", None)
    candidates = [
        raw("https://slack.com", result_url="https://source.example/b", source_title="B"),
        raw("https://www.slack.com/pricing", result_url="https://source.example/a", source_title="A"),
    ]

    first = process_discovery_candidates(company, candidates)
    second = process_discovery_candidates(company, candidates)

    assert first == second


def test_processing_service_is_provider_neutral():
    import app.services.competitor_discovery as processing

    assert "tavily" not in processing.__file__.lower()
    assert not hasattr(processing, "httpx")

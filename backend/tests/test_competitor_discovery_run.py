from datetime import datetime, timezone

import pytest

from app.integrations.competitor_discovery_base import (
    DiscoveryCompanyContext,
    RawDiscoveryCandidate,
)
from app.integrations.competitor_discovery_base import (
    DiscoveryProviderAuthenticationError,
    DiscoveryProviderRateLimitError,
    DiscoveryProviderResponseError,
    DiscoveryProviderTimeoutError,
)
from app.models.competitor import Competitor
from app.models.competitor_discovery_candidate import CompetitorDiscoveryCandidate
from app.models.competitor_discovery_candidate_source import CompetitorDiscoveryCandidateSource
from app.models.competitor_discovery_run import CompetitorDiscoveryRun
from app.models.research_run import ResearchRun
from app.services.competitor_discovery_run import (
    run_competitor_discovery,
)
from app.services import competitor_discovery_run as discovery_run_service
from app.db.session import SessionLocal


class FakeProvider:
    provider_name = "fake"

    def __init__(self, candidates=None, error=None):
        self.candidates = candidates or []
        self.error = error
        self.context = None

    def discover(self, company: DiscoveryCompanyContext):
        self.context = company
        if self.error:
            raise self.error
        return self.candidates


def candidate(url, name="Slack", result_url="https://source.example/result", **kwargs):
    return RawDiscoveryCandidate(
        candidate_name=name,
        candidate_url=url,
        candidate_domain=None,
        supporting_result_url=result_url,
        source_title=kwargs.get("source_title", "Result"),
        source_snippet=kwargs.get("source_snippet", "Snippet"),
        provider_name="fake",
        provider_result_id=kwargs.get("provider_result_id"),
        provider_rank=kwargs.get("provider_rank", 1),
        discovery_method=kwargs.get("discovery_method", "search_competitors"),
    )


def create_research_foundation(db):
    research_run = ResearchRun(input_value="Acme", status="resolving")
    db.add(research_run)
    db.commit()
    db.refresh(research_run)
    from app.models.company_research import CompanyResearch

    company_research = CompanyResearch(
        research_run_id=research_run.id,
        company_name="Acme",
        domain="acme.example",
        industry="SaaS",
        description="Acme description",
    )
    db.add(company_research)
    db.commit()
    return research_run


def test_successful_discovery_persists_candidates_and_provenance(client):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        provider = FakeProvider(
            [
                candidate("https://slack.com", result_url="https://source.example/one"),
                candidate("https://www.slack.com/pricing", result_url="https://source.example/two"),
                candidate("https://notion.so", name="Notion"),
            ]
        )
        discovery_run = run_competitor_discovery(db, research_run.id, provider)

        assert discovery_run.status == "completed"
        assert discovery_run.completed_at is not None
        assert provider.context.domain == "acme.example"
        candidates = db.query(CompetitorDiscoveryCandidate).filter_by(discovery_run_id=discovery_run.id).all()
        sources = db.query(CompetitorDiscoveryCandidateSource).all()
        assert len(candidates) == 2
        assert len(sources) == 2
        slack = next(item for item in candidates if item.domain == "slack.com")
        assert slack.validation_status == "valid"
        assert slack.research_run_id == research_run.id
        assert len(slack.sources) == 2
        assert db.query(Competitor).filter_by(research_run_id=research_run.id).count() == 0
    finally:
        db.close()


def test_persisted_candidates_preserve_discovery_run_ownership(client):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        discovery_run = run_competitor_discovery(
            db,
            research_run.id,
            FakeProvider([candidate("https://slack.com")]),
        )

        candidates = db.query(CompetitorDiscoveryCandidate).filter_by(
            discovery_run_id=discovery_run.id
        ).all()
        assert candidates
        assert all(
            item.research_run_id == discovery_run.research_run_id
            and item.discovery_run_id == discovery_run.id
            for item in candidates
        )
    finally:
        db.close()


def test_m10c_processing_function_is_invoked(client, monkeypatch):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        original_processor = discovery_run_service.process_discovery_candidates
        calls = []

        def processing_spy(company, candidates):
            calls.append((company, candidates))
            return original_processor(company, candidates)

        monkeypatch.setattr(
            discovery_run_service,
            "process_discovery_candidates",
            processing_spy,
        )
        run_competitor_discovery(
            db,
            research_run.id,
            FakeProvider([candidate("https://slack.com")]),
        )

        assert len(calls) == 1
        assert calls[0][0].domain == "acme.example"
        assert len(calls[0][1]) == 1
    finally:
        db.close()


def test_same_company_and_invalid_candidates_are_persisted(client):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        provider = FakeProvider(
            [
                candidate("https://www.acme.example/about", name="Acme"),
                candidate("ftp://invalid.example", name="Broken"),
            ]
        )
        discovery_run = run_competitor_discovery(db, research_run.id, provider)

        assert discovery_run.status == "no_candidates"
        candidates = db.query(CompetitorDiscoveryCandidate).filter_by(discovery_run_id=discovery_run.id).all()
        assert {item.validation_status for item in candidates} == {"same_company", "invalid"}
        assert db.query(Competitor).filter_by(research_run_id=research_run.id).count() == 0
    finally:
        db.close()


@pytest.mark.parametrize(
    ("error", "category"),
    [
        (DiscoveryProviderTimeoutError("timeout"), "timeout"),
        (DiscoveryProviderRateLimitError("rate limit"), "rate_limit"),
        (DiscoveryProviderAuthenticationError("auth"), "authentication"),
        (DiscoveryProviderResponseError("provider"), "provider_error"),
    ],
)
def test_provider_failures_persist_failed_discovery_run(client, error, category):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        discovery_run = run_competitor_discovery(db, research_run.id, FakeProvider(error=error))

        assert discovery_run.status == "failed"
        assert discovery_run.failure_category == category
        assert discovery_run.completed_at is not None
        assert "auth" not in (discovery_run.failure_reason or "")
    finally:
        db.close()


def test_unexpected_provider_error_propagates_and_does_not_leave_run(client):
    db = SessionLocal()
    try:
        research_run = create_research_foundation(db)
        with pytest.raises(RuntimeError, match="unexpected"):
            run_competitor_discovery(
                db,
                research_run.id,
                FakeProvider(error=RuntimeError("unexpected")),
            )
        assert db.query(CompetitorDiscoveryRun).count() == 0
    finally:
        db.close()


def test_discovery_api_rejects_nonexistent_research_run(client):
    response = client.post(
        "/api/research-runs/999999/competitor-discovery"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Research run not found"


def test_discovery_api_returns_structured_candidates_without_provider_configuration(client, monkeypatch):
    research_run = client.post("/api/research", json={"company": "Acme"}).json()
    client.post(f"/api/research/{research_run['research_id']}/resolve")
    client.post(f"/api/research/{research_run['research_id']}/understand")
    provider = FakeProvider([candidate("https://slack.com")])
    monkeypatch.setattr(
        discovery_run_service,
        "TavilyCompetitorDiscoveryProvider",
        lambda: provider,
    )

    response = client.post(
        f"/api/research-runs/{research_run['research_id']}/competitor-discovery"
    )

    assert response.status_code == 202
    submission = response.json()
    assert submission["status"] == "queued"
    body = client.get(submission["status_url"]).json()["result"]
    assert set(body) == {"research_run", "candidates"}
    assert body["research_run"]["provider_name"] == "fake"
    assert body["candidates"][0]["domain"] == "slack.com"
    assert body["candidates"][0]["sources"][0]["source_url"] == "https://source.example/result"
    assert "api_key" not in response.text.lower()


def test_discovery_api_provider_failure_returns_failed_run_without_raw_error(
    client,
    monkeypatch,
):
    research_run = client.post("/api/research", json={"company": "Acme"}).json()
    client.post(f"/api/research/{research_run['research_id']}/resolve")
    client.post(f"/api/research/{research_run['research_id']}/understand")
    raw_error = "rate limit secret provider details"
    provider = FakeProvider(error=DiscoveryProviderRateLimitError(raw_error))
    monkeypatch.setattr(
        discovery_run_service,
        "TavilyCompetitorDiscoveryProvider",
        lambda: provider,
    )

    response = client.post(
        f"/api/research-runs/{research_run['research_id']}/competitor-discovery"
    )

    assert response.status_code == 202
    operation = client.get(response.json()["status_url"]).json()
    assert operation["status"] == "completed"
    body = operation["result"]["research_run"]
    assert body["status"] == "failed"
    assert body["failure_category"] == "rate_limit"
    assert body["failure_reason"] == "Discovery provider rate limit exceeded"
    assert raw_error not in response.text


def test_discovery_api_does_not_accept_client_provider_configuration(
    client,
    monkeypatch,
):
    research_run = client.post("/api/research", json={"company": "Acme"}).json()
    client.post(f"/api/research/{research_run['research_id']}/resolve")
    client.post(f"/api/research/{research_run['research_id']}/understand")
    provider = FakeProvider([candidate("https://slack.com")])
    monkeypatch.setattr(
        discovery_run_service,
        "TavilyCompetitorDiscoveryProvider",
        lambda: provider,
    )

    response = client.post(
        f"/api/research-runs/{research_run['research_id']}/competitor-discovery",
        json={"provider": "attacker", "api_key": "client-secret"},
    )

    assert response.status_code == 202
    operation = client.get(response.json()["status_url"]).json()
    body = operation["result"]
    assert body["research_run"]["provider_name"] == "fake"
    assert "client-secret" not in response.text

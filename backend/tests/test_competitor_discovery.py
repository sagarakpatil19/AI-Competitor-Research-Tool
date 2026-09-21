from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models.competitor_discovery_candidate import CompetitorDiscoveryCandidate
from app.models.competitor_discovery_candidate_source import CompetitorDiscoveryCandidateSource
from app.models.competitor_discovery_run import CompetitorDiscoveryRun
from app.models.competitor import Competitor
from app.models.research_run import ResearchRun
from app.schemas.competitor_discovery import (
    CompetitorDiscoveryCandidateCreate,
    CompetitorDiscoveryCandidateSourceCreate,
    CompetitorDiscoveryRunCreate,
    CompetitorDiscoveryRunResponse,
)


def test_discovery_schemas_accept_foundation_values():
    run = CompetitorDiscoveryRunCreate(research_run_id=1, provider_name="manual")
    candidate = CompetitorDiscoveryCandidateCreate(
        discovery_run_id=1,
        research_run_id=1,
        candidate_name="Slack",
        normalized_name="slack",
        domain="slack.com",
        canonical_url="https://slack.com",
        discovery_method="provider",
        provider_name="provider",
    )
    source = CompetitorDiscoveryCandidateSourceCreate(
        candidate_id=1,
        source_url="https://example.com/result",
        canonical_url="https://example.com/result",
        provider_name="provider",
    )

    assert run.provider_name == "manual"
    assert candidate.validation_status == "pending"
    assert candidate.discovery_status == "received"
    assert source.canonical_url == "https://example.com/result"


def test_discovery_schemas_reject_unknown_statuses():
    with pytest.raises(ValidationError):
        CompetitorDiscoveryRunResponse(
            id=1,
            research_run_id=1,
            provider_name="provider",
            status="unknown",
            failure_category=None,
            failure_reason=None,
            started_at=None,
            completed_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    with pytest.raises(ValidationError):
        CompetitorDiscoveryCandidateCreate(
            discovery_run_id=1,
            research_run_id=1,
            candidate_name="Slack",
            normalized_name="slack",
            discovery_method="provider",
            provider_name="provider",
            validation_status="unknown",
        )


def test_discovery_entities_persist_relationships_and_defaults(client):
    db = SessionLocal()
    try:
        research_run = ResearchRun(input_value="Acme", status="submitted")
        db.add(research_run)
        db.commit()
        db.refresh(research_run)

        discovery_run = CompetitorDiscoveryRun(
            research_run_id=research_run.id,
            provider_name="provider",
        )
        db.add(discovery_run)
        db.commit()
        db.refresh(discovery_run)

        candidate = CompetitorDiscoveryCandidate(
            discovery_run_id=discovery_run.id,
            research_run_id=research_run.id,
            candidate_name="Slack",
            normalized_name="slack",
            domain="slack.com",
            canonical_url="https://slack.com",
            discovery_method="provider",
            provider_name="provider",
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        source = CompetitorDiscoveryCandidateSource(
            candidate_id=candidate.id,
            source_url="https://example.com/slack",
            canonical_url="https://example.com/slack",
            source_title="Slack result",
            source_snippet="Supporting result",
            provider_name="provider",
            provider_rank=1,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        stored_run = db.get(CompetitorDiscoveryRun, discovery_run.id)
        stored_candidate = db.get(CompetitorDiscoveryCandidate, candidate.id)
        stored_source = db.get(CompetitorDiscoveryCandidateSource, source.id)

        assert stored_run is not None
        assert stored_run.status == "pending"
        assert stored_run.research_run_id == research_run.id
        assert stored_candidate is not None
        assert stored_candidate.discovery_status == "received"
        assert stored_candidate.validation_status == "pending"
        assert stored_candidate.discovery_run_id == stored_run.id
        assert stored_source is not None
        assert stored_source.candidate_id == stored_candidate.id
        assert stored_candidate.sources[0].id == stored_source.id
        assert stored_run.candidates[0].id == stored_candidate.id
        assert research_run.discovery_runs[0].id == stored_run.id
        assert research_run.discovery_candidates[0].id == stored_candidate.id
    finally:
        db.close()


def test_multiple_domainless_candidates_are_persistable(client):
    db = SessionLocal()
    try:
        research_run = ResearchRun(input_value="Acme", status="submitted")
        db.add(research_run)
        db.commit()
        db.refresh(research_run)
        discovery_run = CompetitorDiscoveryRun(
            research_run_id=research_run.id,
            provider_name="provider",
            started_at=datetime.now(timezone.utc),
        )
        db.add(discovery_run)
        db.commit()
        db.refresh(discovery_run)

        candidates = [
            CompetitorDiscoveryCandidate(
                discovery_run_id=discovery_run.id,
                research_run_id=research_run.id,
                candidate_name=f"Candidate {index}",
                normalized_name=f"candidate-{index}",
                domain=None,
                discovery_method="provider",
                provider_name="provider",
            )
            for index in (1, 2)
        ]
        db.add_all(candidates)
        db.commit()

        stored = list(
            db.scalars(
                select(CompetitorDiscoveryCandidate).where(
                    CompetitorDiscoveryCandidate.research_run_id == research_run.id
                )
            ).all()
        )
        assert len(stored) == 2
    finally:
        db.close()


def _create_discovery_entities(db, domain="slack.com"):
    research_run = ResearchRun(input_value="Acme", status="submitted")
    db.add(research_run)
    db.commit()
    db.refresh(research_run)

    discovery_run = CompetitorDiscoveryRun(
        research_run_id=research_run.id,
        provider_name="provider",
    )
    db.add(discovery_run)
    db.commit()
    db.refresh(discovery_run)

    candidate = CompetitorDiscoveryCandidate(
        discovery_run_id=discovery_run.id,
        research_run_id=research_run.id,
        candidate_name="Slack",
        normalized_name="slack",
        domain=domain,
        discovery_method="provider",
        provider_name="provider",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return research_run, discovery_run, candidate


def _create_candidate_source(db, candidate_id, canonical_url):
    source = CompetitorDiscoveryCandidateSource(
        candidate_id=candidate_id,
        source_url=canonical_url,
        canonical_url=canonical_url,
        provider_name="provider",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def test_same_research_run_and_domain_is_rejected(client):
    db = SessionLocal()
    try:
        _, discovery_run, first = _create_discovery_entities(db)
        duplicate = CompetitorDiscoveryCandidate(
            discovery_run_id=discovery_run.id,
            research_run_id=first.research_run_id,
            candidate_name="Slack duplicate",
            normalized_name="slack-duplicate",
            domain="slack.com",
            discovery_method="provider",
            provider_name="provider",
        )
        db.add(duplicate)

        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        assert db.get(CompetitorDiscoveryCandidate, first.id) is not None
    finally:
        db.close()


def test_same_domain_is_allowed_for_different_research_runs(client):
    db = SessionLocal()
    try:
        _, _, first = _create_discovery_entities(db)
        _, _, second = _create_discovery_entities(db)

        assert first.domain == second.domain
        assert first.research_run_id != second.research_run_id
    finally:
        db.close()


def test_same_candidate_and_canonical_url_is_rejected(client):
    db = SessionLocal()
    try:
        _, _, candidate = _create_discovery_entities(db)
        _create_candidate_source(db, candidate.id, "https://example.com/result")
        duplicate = CompetitorDiscoveryCandidateSource(
            candidate_id=candidate.id,
            source_url="https://example.com/result",
            canonical_url="https://example.com/result",
            provider_name="provider",
        )
        db.add(duplicate)

        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

        assert len(candidate.sources) == 1
    finally:
        db.close()


def test_same_canonical_url_is_allowed_for_different_candidates(client):
    db = SessionLocal()
    try:
        _, discovery_run, first = _create_discovery_entities(db, domain="first.example")
        second = CompetitorDiscoveryCandidate(
            discovery_run_id=discovery_run.id,
            research_run_id=first.research_run_id,
            candidate_name="Second",
            normalized_name="second",
            domain="second.example",
            discovery_method="provider",
            provider_name="provider",
        )
        db.add(second)
        db.commit()
        db.refresh(second)

        first_source = _create_candidate_source(db, first.id, "https://example.com/result")
        second_source = _create_candidate_source(db, second.id, "https://example.com/result")

        assert first_source.id != second_source.id
    finally:
        db.close()


def test_deleting_discovery_run_cascades_candidates_and_sources(client):
    db = SessionLocal()
    try:
        _, discovery_run, candidate = _create_discovery_entities(db)
        source = _create_candidate_source(db, candidate.id, "https://example.com/result")
        discovery_run_id = discovery_run.id
        candidate_id = candidate.id
        source_id = source.id

        db.delete(discovery_run)
        db.commit()

        assert db.get(CompetitorDiscoveryRun, discovery_run_id) is None
        assert db.get(CompetitorDiscoveryCandidate, candidate_id) is None
        assert db.get(CompetitorDiscoveryCandidateSource, source_id) is None
    finally:
        db.close()


def test_deleting_competitor_nulls_candidate_competitor_id(client):
    db = SessionLocal()
    try:
        _, _, candidate = _create_discovery_entities(db)
        competitor = Competitor(
            research_run_id=candidate.research_run_id,
            name="Slack",
            domain="slack.com",
        )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
        candidate.competitor_id = competitor.id
        db.commit()

        candidate_id = candidate.id
        db.delete(competitor)
        db.commit()

        preserved = db.get(CompetitorDiscoveryCandidate, candidate_id)
        assert preserved is not None
        assert preserved.competitor_id is None
    finally:
        db.close()

from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    CompanyResearch,
    Competitor,
    CompetitorEvidence,
    CompetitorResearchFact,
    CompetitorResearchSection,
    ResearchInputType,
    ResearchRun,
    ResearchRunStatus,
)
from app.repositories import competitor_research as competitor_research_repository
from app.services import research as research_service
from app.services.competitor_research_structuring import structure_competitor_research


def make_db() -> tuple[object, Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def create_research_context(db: Session, name: str = "Acme") -> tuple[ResearchRun, Competitor]:
    research_run = ResearchRun(
        input_value=name,
        input_type=ResearchInputType.COMPANY_NAME,
        status=ResearchRunStatus.RESOLVING,
    )
    db.add(research_run)
    db.flush()
    db.add(CompanyResearch(research_run_id=research_run.id, company_name=name))
    competitor = Competitor(research_run_id=research_run.id, name="Competitor", domain="competitor.example")
    db.add(competitor)
    db.commit()
    db.refresh(research_run)
    db.refresh(competitor)
    return research_run, competitor


def create_execution(db: Session, research_run: ResearchRun, competitor: Competitor):
    return research_service.create_competitor_research_execution(db, research_run, competitor.id)


def test_first_and_second_calls_create_distinct_pending_executions():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)

        first = research_service.research_competitors(db, research_run, [competitor.id])[0]
        second = research_service.research_competitors(db, research_run, [competitor.id])[0]

        assert first.id != second.id
        assert first.status == "pending"
        assert second.status == "pending"
        assert first.started_at is None
        assert second.started_at is None
        assert first.research_run_id == research_run.id
        assert second.research_run_id == research_run.id
    finally:
        db.close()
        engine.dispose()


def test_new_execution_does_not_modify_historical_data():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        first = create_execution(db, research_run, competitor)
        first.failure_reason = None
        first.description = "Historical summary"
        first.status = "completed"
        first.started_at = datetime(2026, 9, 21, 10, 0, 0)
        first.completed_at = datetime(2026, 9, 21, 10, 1, 0)
        evidence = CompetitorEvidence(
            competitor_research_id=first.id,
            source_url="https://competitor.example/about",
            content="The company was founded in 2018.",
        )
        fact = CompetitorResearchFact(
            competitor_research_id=first.id,
            section="company_overview",
            fact_type="founded_year",
            value_numeric=2018,
            normalized_key="company_overview:founded_year",
        )
        section = CompetitorResearchSection(
            competitor_research_id=first.id,
            section="company_overview",
            status="structured",
            fact_count=1,
        )
        db.add_all([evidence, fact, section])
        db.commit()
        historical = (first.status, first.started_at, first.completed_at, first.description)

        second = create_execution(db, research_run, competitor)
        db.expire_all()
        unchanged = db.get(type(first), first.id)

        assert second.id != first.id
        assert (unchanged.status, unchanged.started_at, unchanged.completed_at, unchanged.description) == historical
        assert db.scalar(select(CompetitorEvidence.id).where(CompetitorEvidence.competitor_research_id == first.id)) == evidence.id
        assert db.scalar(select(CompetitorResearchFact.id).where(CompetitorResearchFact.competitor_research_id == first.id)) == fact.id
        assert db.scalar(select(CompetitorResearchSection.id).where(CompetitorResearchSection.competitor_research_id == first.id)) == section.id
    finally:
        db.close()
        engine.dispose()


def test_cross_research_run_execution_is_rejected():
    engine, db = make_db()
    try:
        first_run, first_competitor = create_research_context(db, "First")
        second_run, _ = create_research_context(db, "Second")
        execution = create_execution(db, first_run, first_competitor)

        with pytest.raises(ValueError, match="must belong to the research run"):
            research_service.get_competitor_research_execution(db, second_run, execution.id)
    finally:
        db.close()
        engine.dispose()


def test_collecting_transition_sets_started_at_only_when_started():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        execution = create_execution(db, research_run, competitor)
        assert execution.status == "pending"
        assert execution.started_at is None

        started = research_service.start_competitor_research_collection(
            db, research_run, execution.id
        )

        assert started.status == "collecting"
        assert started.started_at is not None
        assert started.completed_at is None
    finally:
        db.close()
        engine.dispose()


def test_explicit_source_targeting_does_not_use_latest_execution():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        first = create_execution(db, research_run, competitor)
        second = create_execution(db, research_run, competitor)

        source, created = research_service.register_competitor_source(
            db,
            research_run,
            competitor.id,
            {"source_url": "https://competitor.example/second"},
            competitor_research_id=first.id,
        )

        assert created is True
        assert source.competitor_research_id == first.id
        assert second.id != first.id
    finally:
        db.close()
        engine.dispose()


def test_structuring_completes_selected_execution():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        execution = create_execution(db, research_run, competitor)
        research_service.start_competitor_research_collection(db, research_run, execution.id)
        db.add(
            CompetitorEvidence(
                competitor_research_id=execution.id,
                source_url="https://competitor.example/about",
                content="The company was founded in 2018.",
                normalized_content="The company was founded in 2018.",
                processing_status="processed",
                validation_status="valid",
            )
        )
        db.commit()

        completed = structure_competitor_research(db, research_run, execution.id)

        assert completed.status == "completed"
        assert completed.started_at is not None
        assert completed.completed_at is not None
    finally:
        db.close()
        engine.dispose()


def test_failure_affects_only_selected_execution():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        first = create_execution(db, research_run, competitor)
        second = create_execution(db, research_run, competitor)

        failed = research_service.fail_competitor_research_execution(
            db,
            research_run,
            first.id,
            "Source collection failed",
        )

        assert failed.status == "failed"
        assert failed.failure_reason == "Source collection failed"
        assert db.get(type(second), second.id).status == "pending"
        assert db.get(type(second), second.id).failure_reason is None
    finally:
        db.close()
        engine.dispose()


def test_latest_execution_repository_methods_remain_latest():
    engine, db = make_db()
    try:
        research_run, competitor = create_research_context(db)
        first = create_execution(db, research_run, competitor)
        second = create_execution(db, research_run, competitor)

        assert competitor_research_repository.get_by_competitor_id(db, competitor.id).id == second.id
        assert competitor_research_repository.get_by_competitor_ids(db, [competitor.id])[0].id == second.id
        assert first.id != second.id
    finally:
        db.close()
        engine.dispose()

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
import pytest

from app.db.base import Base
from app.models import (
    CompetitorEvidence,
    CompetitorResearchFact,
    CompetitorResearchFactEvidence,
    CompetitorResearchSection,
)
from app.services.competitor_research_structuring import structure_competitor_research
from tests.test_competitor_research_models import create_execution


def make_db() -> tuple[object, Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def add_evidence(
    db: Session,
    execution_id: int,
    content: str,
    *,
    processing_status: str = "processed",
    validation_status: str = "valid",
    source_type: str | None = None,
) -> CompetitorEvidence:
    evidence = CompetitorEvidence(
        competitor_research_id=execution_id,
        source_url="https://acme.example/research",
        source_type=source_type,
        content=content,
        normalized_content=content,
        processing_status=processing_status,
        validation_status=validation_status,
    )
    db.add(evidence)
    db.flush()
    return evidence


def test_valid_evidence_creates_fact_and_provenance():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        evidence = add_evidence(db, execution.id, "Plans start at $29 per month.")

        structure_competitor_research(db, research_run, execution.id)

        fact = db.scalar(select(CompetitorResearchFact))
        link = db.scalar(select(CompetitorResearchFactEvidence))
        assert fact is not None
        assert fact.section == "pricing"
        assert fact.fact_type == "starting_price"
        assert fact.value_numeric == 29
        assert fact.currency == "USD"
        assert fact.unit == "month"
        assert fact.normalized_key == "pricing:starting_price:month"
        assert link is not None
        assert link.fact_id == fact.id
        assert link.evidence_id == evidence.id
        assert link.citation_excerpt == "Plans start at $29 per month."
    finally:
        db.close()
        engine.dispose()


def test_euro_pricing_creates_eur_fact_with_provenance():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        evidence = add_evidence(db, execution.id, "Plans start at €29 per month.")

        structure_competitor_research(db, research_run, execution.id)

        fact = db.scalar(select(CompetitorResearchFact))
        link = db.scalar(select(CompetitorResearchFactEvidence))
        assert fact is not None
        assert fact.section == "pricing"
        assert fact.fact_type == "starting_price"
        assert fact.value_numeric == 29
        assert fact.currency == "EUR"
        assert fact.unit == "month"
        assert link is not None
        assert link.fact_id == fact.id
        assert link.evidence_id == evidence.id
    finally:
        db.close()
        engine.dispose()


def test_pound_pricing_creates_gbp_fact_with_provenance():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        evidence = add_evidence(db, execution.id, "Plans start at £49 per month.")

        structure_competitor_research(db, research_run, execution.id)

        fact = db.scalar(select(CompetitorResearchFact))
        link = db.scalar(select(CompetitorResearchFactEvidence))
        assert fact is not None
        assert fact.section == "pricing"
        assert fact.fact_type == "starting_price"
        assert fact.value_numeric == 49
        assert fact.currency == "GBP"
        assert fact.unit == "month"
        assert link is not None
        assert link.fact_id == fact.id
        assert link.evidence_id == evidence.id
    finally:
        db.close()
        engine.dispose()


def test_invalid_pending_and_duplicate_evidence_produce_no_facts():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "The company was founded in 2018.", validation_status="invalid")
        add_evidence(db, execution.id, "The company was founded in 2018.", processing_status="pending")
        add_evidence(db, execution.id, "The company was founded in 2018.", validation_status="duplicate")

        structure_competitor_research(db, research_run, execution.id)

        assert db.scalar(select(func.count(CompetitorResearchFact.id))) == 0
    finally:
        db.close()
        engine.dispose()


def test_unsupported_valid_text_sets_no_evidence_without_inventing_facts():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "Acme is a company with information available online.")

        structure_competitor_research(db, research_run, execution.id)

        sections = db.scalars(select(CompetitorResearchSection)).all()
        overview = next(section for section in sections if section.section == "company_overview")
        assert overview.status == "no_evidence"
        assert overview.fact_count == 0
        assert overview.reason == "No deterministic structured fact was extracted from valid evidence."
    finally:
        db.close()
        engine.dispose()


def test_product_and_feature_extraction_is_deterministic():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "Acme offers CRM, marketing automation, and analytics.")
        add_evidence(db, execution.id, "Acme supports SSO and audit logs.")

        structure_competitor_research(db, research_run, execution.id)

        facts = db.scalars(select(CompetitorResearchFact)).all()
        assert {(fact.section, fact.fact_type, fact.subject) for fact in facts} == {
            ("products", "product", "CRM"),
            ("products", "product", "marketing automation"),
            ("products", "product", "analytics"),
            ("features", "feature", "SSO"),
            ("features", "feature", "audit logs"),
        }
    finally:
        db.close()
        engine.dispose()


def test_customer_feedback_does_not_classify_sentiment():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(
            db,
            execution.id,
            "Customers love the product and say it is excellent.",
            source_type="article",
        )

        structure_competitor_research(db, research_run, execution.id)

        assert db.scalar(select(func.count(CompetitorResearchFact.id))) == 0
    finally:
        db.close()
        engine.dispose()


def test_target_audience_and_customer_feedback_metadata_are_structured_without_sentiment():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(
            db,
            execution.id,
            "Acme is designed for enterprise teams. It has a 4.5 out of 5 rating from 120 reviews on G2.",
        )

        structure_competitor_research(db, research_run, execution.id)

        facts = db.scalars(select(CompetitorResearchFact)).all()
        assert {(fact.section, fact.fact_type, fact.subject, fact.value_numeric) for fact in facts} == {
            ("target_audience", "audience", "enterprise teams", None),
            ("customer_feedback", "rating", None, 4.5),
            ("customer_feedback", "review_count", None, 120),
            ("customer_feedback", "review_platform", "G2", None),
        }
        assert all(fact.fact_type not in {"sentiment", "satisfaction"} for fact in facts)
    finally:
        db.close()
        engine.dispose()


def test_free_pricing_is_structured_without_numeric_inference():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "The starter plan is free for small teams.")

        structure_competitor_research(db, research_run, execution.id)

        fact = db.scalar(select(CompetitorResearchFact))
        assert fact is not None
        assert fact.fact_type == "free_plan"
        assert fact.value_text == "Free"
        assert fact.value_numeric is None
    finally:
        db.close()
        engine.dispose()


def test_structuring_rejects_execution_from_another_research_run():
    engine, db = make_db()
    try:
        first_run, _, first_execution = create_execution(db, "First")
        second_run, _, _ = create_execution(db, "Second")

        with pytest.raises(ValueError, match="must belong to the research run"):
            structure_competitor_research(db, second_run, first_execution.id)
        assert first_run.id != second_run.id
    finally:
        db.close()
        engine.dispose()


def test_conflicting_explicit_prices_are_preserved_with_distinct_keys():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "Plans start at $29 per month.")
        add_evidence(db, execution.id, "Plans start at $49 per month.")

        structure_competitor_research(db, research_run, execution.id)

        facts = db.scalars(select(CompetitorResearchFact)).all()
        assert {(fact.value_numeric, fact.normalized_key) for fact in facts} == {
            (29, "pricing:starting_price:month"),
            (49, "pricing:starting_price:month:value:49_usd"),
        }
        assert db.scalar(select(func.count(CompetitorResearchFactEvidence.fact_id))) == 2
    finally:
        db.close()
        engine.dispose()


def test_sections_are_structured_and_counts_are_fact_counts():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "The company was founded in 2018.")

        structure_competitor_research(db, research_run, execution.id)

        sections = db.scalars(select(CompetitorResearchSection)).all()
        assert {section.section for section in sections} == {
            "company_overview",
            "products",
            "features",
            "pricing",
            "target_audience",
            "customer_feedback",
        }
        overview = next(section for section in sections if section.section == "company_overview")
        assert overview.status == "structured"
        assert overview.fact_count == 1
    finally:
        db.close()
        engine.dispose()


def test_structuring_is_idempotent_and_does_not_duplicate_links():
    engine, db = make_db()
    try:
        research_run, _, execution = create_execution(db)
        add_evidence(db, execution.id, "The company was founded in 2018.")

        structure_competitor_research(db, research_run, execution.id)
        structure_competitor_research(db, research_run, execution.id)

        assert db.scalar(select(func.count(CompetitorResearchFact.id))) == 1
        assert db.scalar(select(func.count(CompetitorResearchFactEvidence.fact_id))) == 1
    finally:
        db.close()
        engine.dispose()


def test_facts_do_not_leak_between_executions_and_historical_facts_remain():
    engine, db = make_db()
    try:
        research_run, competitor, first = create_execution(db)
        second = type(first)(competitor_id=competitor.id, research_run_id=research_run.id)
        db.add(second)
        db.flush()
        add_evidence(db, first.id, "The company was founded in 2018.")
        add_evidence(db, second.id, "Plans start at $49 per month.")

        structure_competitor_research(db, research_run, first.id)
        structure_competitor_research(db, research_run, second.id)

        first_facts = db.scalars(
            select(CompetitorResearchFact).where(CompetitorResearchFact.competitor_research_id == first.id)
        ).all()
        second_facts = db.scalars(
            select(CompetitorResearchFact).where(CompetitorResearchFact.competitor_research_id == second.id)
        ).all()
        assert [(fact.fact_type, fact.value_numeric) for fact in first_facts] == [("founded_year", 2018)]
        assert [(fact.fact_type, fact.value_numeric) for fact in second_facts] == [("starting_price", 49)]
    finally:
        db.close()
        engine.dispose()

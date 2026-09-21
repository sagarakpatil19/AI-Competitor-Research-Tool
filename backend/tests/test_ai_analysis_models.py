import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    AIAnalysis,
    AIAnalysisInputEvidence,
    AIAnalysisInputFact,
    AIComparison,
    AIComparisonCompetitor,
    AIStatement,
    AIStatementEvidence,
    AIStatementFact,
    Competitor,
    CompetitorEvidence,
    CompetitorResearch,
    CompetitorResearchFact,
    ResearchRun,
)
from app.repositories import ai_analyses, ai_comparisons, ai_statements


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def create_context(db: Session) -> tuple[ResearchRun, CompetitorResearch, CompetitorResearchFact, CompetitorEvidence]:
    research_run = ResearchRun(input_value="Acme")
    db.add(research_run)
    db.flush()
    competitor = Competitor(research_run_id=research_run.id, name="Competitor", domain="competitor.example")
    db.add(competitor)
    db.flush()
    execution = CompetitorResearch(
        competitor_id=competitor.id,
        research_run_id=research_run.id,
    )
    db.add(execution)
    db.flush()
    fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="pricing",
        fact_type="starting_price",
        value_numeric=29,
        currency="USD",
        unit="month",
        normalized_key="pricing:starting_price:month",
    )
    evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_url="https://competitor.example/pricing",
        content="Plans start at $29 per month.",
        normalized_content="Plans start at $29 per month.",
        normalized_content_hash="a" * 64,
        processing_status="processed",
        validation_status="valid",
    )
    db.add_all([fact, evidence])
    db.flush()
    return research_run, execution, fact, evidence


def make_analysis(research_run_id: int, competitor_research_id: int | None, scope: str = "competitor") -> AIAnalysis:
    return AIAnalysis(
        research_run_id=research_run_id,
        competitor_research_id=competitor_research_id,
        scope=scope,
        provider_name="test-provider",
        model_name="test-model",
        prompt_version="prompt-v1",
        contract_version="contract-v1",
    )


def test_competitor_and_research_run_analysis_scopes_are_persisted(db: Session):
    research_run, execution, _, _ = create_context(db)
    competitor_analysis = make_analysis(research_run.id, execution.id)
    run_analysis = make_analysis(research_run.id, None, "research_run")
    db.add_all([competitor_analysis, run_analysis])
    db.commit()

    assert competitor_analysis.competitor_research_id == execution.id
    assert competitor_analysis.scope == "competitor"
    assert run_analysis.competitor_research_id is None
    assert run_analysis.scope == "research_run"
    assert ai_analyses.list_by_research_run_id(db, research_run.id) == [competitor_analysis, run_analysis]


def test_analysis_scope_requires_matching_competitor_research_presence(db: Session):
    research_run, execution, _, _ = create_context(db)

    db.add(make_analysis(research_run.id, None, "competitor"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add(make_analysis(research_run.id, execution.id, "research_run"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    db.add_all(
        [
            make_analysis(research_run.id, execution.id, "competitor"),
            make_analysis(research_run.id, None, "research_run"),
        ]
    )
    db.commit()


def test_multiple_analysis_executions_can_target_same_competitor_research(db: Session):
    research_run, execution, _, _ = create_context(db)
    first = make_analysis(research_run.id, execution.id)
    second = make_analysis(research_run.id, execution.id)
    first.status = "completed"
    second.status = "completed"
    db.add_all([first, second])
    db.commit()

    stored = db.scalars(
        select(AIAnalysis).where(AIAnalysis.competitor_research_id == execution.id)
    ).all()
    assert len(stored) == 2
    assert {analysis.id for analysis in stored} == {first.id, second.id}
    assert all(analysis.status == "completed" for analysis in stored)


def test_analysis_lifecycle_and_metadata_are_persisted(db: Session):
    research_run, execution, _, _ = create_context(db)
    analysis = make_analysis(research_run.id, execution.id)
    db.add(analysis)
    db.commit()
    analysis.status = "running"
    analysis.input_snapshot_hash = "b" * 64
    db.commit()
    analysis.status = "completed"
    db.commit()

    stored = ai_analyses.get_analysis(db, analysis.id)
    assert stored is not None
    assert stored.status == "completed"
    assert stored.input_snapshot_hash == "b" * 64
    assert stored.provider_name == "test-provider"


def test_all_input_and_output_provenance_relationships_are_explicit(db: Session):
    research_run, execution, fact, evidence = create_context(db)
    analysis = make_analysis(research_run.id, execution.id)
    db.add(analysis)
    db.flush()
    input_fact = AIAnalysisInputFact(analysis_id=analysis.id, fact_id=fact.id)
    input_evidence = AIAnalysisInputEvidence(
        analysis_id=analysis.id,
        evidence_id=evidence.id,
        content_hash=evidence.normalized_content_hash,
        normalized_excerpt=evidence.normalized_excerpt,
    )
    statement = AIStatement(
        analysis_id=analysis.id,
        statement_type="observation",
        text="The listed starting price is $29 per month.",
        support_status="supported",
        competitor_research_id=execution.id,
        section="pricing",
    )
    db.add_all([input_fact, input_evidence, statement])
    db.flush()
    statement_fact = AIStatementFact(statement_id=statement.id, fact_id=fact.id, role="supports")
    statement_evidence = AIStatementEvidence(
        statement_id=statement.id,
        evidence_id=evidence.id,
        citation_excerpt="Plans start at $29 per month.",
        role="quotes",
    )
    comparison = AIComparison(
        analysis_id=analysis.id,
        comparison_type="pricing",
        dimension="starting_price",
        statement="Pricing comparison requires multiple competitor executions.",
        support_status="insufficient_evidence",
    )
    db.add_all([statement_fact, statement_evidence, comparison])
    db.flush()
    comparison_competitor = AIComparisonCompetitor(
        comparison_id=comparison.id,
        competitor_research_id=execution.id,
        role="subject",
    )
    db.add(comparison_competitor)
    db.commit()

    assert analysis.input_facts[0].fact.id == fact.id
    assert analysis.input_evidence[0].evidence.id == evidence.id
    assert statement.fact_links[0].fact.id == fact.id
    assert statement.evidence_links[0].evidence.id == evidence.id
    assert comparison.competitors[0].competitor_research_id == execution.id
    assert ai_statements.list_by_analysis_id(db, analysis.id)[0].id == statement.id
    assert ai_comparisons.list_by_analysis_id(db, analysis.id)[0].id == comparison.id


def test_duplicate_input_and_output_associations_are_rejected(db: Session):
    research_run, execution, fact, evidence = create_context(db)
    analysis = make_analysis(research_run.id, execution.id)
    db.add(analysis)
    db.flush()
    db.add(AIAnalysisInputFact(analysis_id=analysis.id, fact_id=fact.id))
    db.commit()

    db.add(AIAnalysisInputFact(analysis_id=analysis.id, fact_id=fact.id))
    with pytest.raises(IntegrityError):
        db.commit()


def test_statement_type_status_and_role_constraints_are_rejected(db: Session):
    research_run, execution, fact, _ = create_context(db)
    analysis = make_analysis(research_run.id, execution.id)
    db.add(analysis)
    db.flush()
    db.add(
        AIStatement(
            analysis_id=analysis.id,
            statement_type="unsupported",
            text="Invalid",
            support_status="supported",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    statement = AIStatement(
        analysis_id=analysis.id,
        statement_type="observation",
        text="Valid",
        support_status="supported",
    )
    db.add(statement)
    db.flush()
    db.add(AIStatementFact(statement_id=statement.id, fact_id=fact.id, role="unsupported"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_comparison_competitor_uniqueness_is_enforced(db: Session):
    research_run, execution, _, _ = create_context(db)
    analysis = make_analysis(research_run.id, None, "research_run")
    db.add(analysis)
    db.flush()
    comparison = AIComparison(
        analysis_id=analysis.id,
        comparison_type="features",
        dimension="feature",
        statement="Comparison",
        support_status="supported",
    )
    db.add(comparison)
    db.flush()
    db.add_all(
        [
            AIComparisonCompetitor(comparison_id=comparison.id, competitor_research_id=execution.id, role="subject"),
            AIComparisonCompetitor(comparison_id=comparison.id, competitor_research_id=execution.id, role="compared"),
        ]
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_fact_and_evidence_inputs_can_be_snapshotted_without_output_fact(db: Session):
    research_run, execution, fact, evidence = create_context(db)
    analysis = make_analysis(research_run.id, execution.id)
    db.add(analysis)
    db.flush()
    db.add(
        AIAnalysisInputEvidence(
            analysis_id=analysis.id,
            evidence_id=evidence.id,
            content_hash=evidence.normalized_content_hash,
            normalized_excerpt=evidence.normalized_excerpt,
        )
    )
    db.commit()

    assert len(analysis.input_evidence) == 1
    assert len(analysis.input_facts) == 0
    assert fact.competitor_research_id == execution.id

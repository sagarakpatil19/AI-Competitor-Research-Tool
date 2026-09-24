from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.contracts import AIComparisonResult, AIStatementResult, ProviderAnalysisResult
from app.ai.errors import ProviderUnavailableError
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
    CompetitorSource,
    ResearchRun,
)
from app.models.competitor_research_section import CompetitorResearchSection
from app.services.ai_analysis import execute_ai_analysis


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class FakeProvider:
    def analyze(self, context):
        return ProviderAnalysisResult(
            scope=context.scope,
            provider="fake-provider",
            model="fake-model",
            statements=[
                AIStatementResult(
                    statement_id="STATEMENT_001",
                    statement_type="observation",
                    text="Pricing differs across competitors.",
                    support_status="supported",
                    competitor_context_id=context.competitors[0].context_id,
                    fact_context_ids=[context.facts[0].context_id],
                    evidence_context_ids=[context.evidence[0].context_id],
                    source_context_ids=[context.sources[0].context_id],
                    fact_roles={context.facts[0].context_id: "supports"},
                    evidence_roles={context.evidence[0].context_id: "quotes"},
                )
            ],
            comparisons=[
                AIComparisonResult(
                    comparison_id="COMPARISON_001",
                    comparison_type="pricing",
                    dimension="starting_price",
                    statement="Pricing comparison across competitors.",
                    support_status="supported",
                    competitor_context_ids=[item.context_id for item in context.competitors],
                    fact_context_ids=[item.context_id for item in context.facts],
                    evidence_context_ids=[item.context_id for item in context.evidence],
                    source_context_ids=[item.context_id for item in context.sources],
                    competitor_roles={
                        context.competitors[0].context_id: "subject",
                        context.competitors[1].context_id: "compared",
                    },
                )
            ],
        )


def make_execution(db: Session, run: ResearchRun, name: str, domain: str, amount: Decimal):
    competitor = Competitor(research_run_id=run.id, name=name, domain=domain)
    db.add(competitor)
    db.flush()
    execution = CompetitorResearch(competitor_id=competitor.id, research_run_id=run.id)
    db.add(execution)
    db.flush()
    fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="pricing",
        fact_type="starting_price",
        value_numeric=amount,
        currency="USD",
        unit="month",
        normalized_key=f"pricing:starting_price:month:{amount}",
    )
    evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_url=f"https://{domain}/pricing",
        content=f"Plans start at ${amount} per month.",
        normalized_content=f"Plans start at ${amount} per month.",
        normalized_content_hash="a" * 64,
        processing_status="processed",
        validation_status="valid",
    )
    source = CompetitorSource(
        competitor_research_id=execution.id,
        canonical_url=f"https://{domain}/pricing",
        source_type="pricing",
        discovery_method="manual",
        status="collected",
    )
    db.add_all([fact, source, evidence])
    db.flush()
    evidence.source_id = source.id
    for section_name in (
        "company_overview",
        "products",
        "features",
        "pricing",
        "target_audience",
        "customer_feedback",
    ):
        db.add(CompetitorResearchSection(competitor_research_id=execution.id, section=section_name))
    db.flush()
    from app.models.competitor_research_fact_evidence import CompetitorResearchFactEvidence
    db.add(CompetitorResearchFactEvidence(fact_id=fact.id, evidence_id=evidence.id))
    db.commit()
    return execution, fact, evidence


def test_execute_ai_analysis_persists_provider_output(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()

    first_execution, first_fact, first_evidence = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    second_execution, second_fact, second_evidence = make_execution(db, run, "Beta", "beta.example", Decimal("49"))

    analysis = execute_ai_analysis(
        db,
        run.id,
        provider=FakeProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )

    assert analysis.status == "completed"
    assert analysis.provider_name == "fake-provider"
    assert analysis.model_name == "fake-model"
    assert analysis.input_snapshot_hash
    assert len(analysis.input_facts) == 2
    assert len(analysis.input_evidence) == 2
    assert len(analysis.statements) == 1
    assert len(analysis.comparisons) == 1
    assert analysis.statements[0].fact_links[0].fact_id in {first_fact.id, second_fact.id}
    assert analysis.comparisons[0].competitors[0].role in {"subject", "compared"}


def test_research_run_analysis_rejects_execution_from_another_research_run(db: Session):
    first_run = ResearchRun(input_value="Acme")
    second_run = ResearchRun(input_value="Beta Corp")
    db.add_all([first_run, second_run])
    db.flush()
    first_execution, _, _ = make_execution(db, first_run, "Alpha", "alpha.example", Decimal("29"))
    second_execution, _, _ = make_execution(db, second_run, "Beta", "beta.example", Decimal("49"))

    class RecordingProvider:
        def __init__(self):
            self.calls = 0

        def analyze(self, context):
            self.calls += 1
            return FakeProvider().analyze(context)

    provider = RecordingProvider()
    analysis = execute_ai_analysis(
        db,
        first_run.id,
        provider=provider,
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )

    assert analysis.status == "failed"
    assert "must belong to the research run" in analysis.failure_reason
    assert provider.calls == 0
    stored = db.scalars(select(AIAnalysis).where(AIAnalysis.research_run_id == first_run.id)).all()
    assert len(stored) == 1
    assert all(item.status != "completed" for item in stored)
    assert analysis.competitor_research_id is None


def test_persistence_failure_rolls_back_partial_analysis_output(db: Session, monkeypatch):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    first_execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    second_execution, _, _ = make_execution(db, run, "Beta", "beta.example", Decimal("49"))

    def fail_after_partial_persistence(*args, **kwargs):
        raise RuntimeError("comparison persistence failed")

    monkeypatch.setattr("app.services.ai_analysis._persist_comparisons", fail_after_partial_persistence)

    analysis = execute_ai_analysis(
        db,
        run.id,
        provider=FakeProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )

    assert analysis.status == "failed"
    assert "comparison persistence failed" in analysis.failure_reason
    assert db.scalars(select(AIAnalysisInputFact).where(AIAnalysisInputFact.analysis_id == analysis.id)).all() == []
    assert db.scalars(select(AIAnalysisInputEvidence).where(AIAnalysisInputEvidence.analysis_id == analysis.id)).all() == []
    statements = db.scalars(select(AIStatement).where(AIStatement.analysis_id == analysis.id)).all()
    comparisons = db.scalars(select(AIComparison).where(AIComparison.analysis_id == analysis.id)).all()
    assert statements == []
    assert comparisons == []
    assert db.scalars(select(AIStatementFact)).all() == []
    assert db.scalars(select(AIStatementEvidence)).all() == []
    assert db.scalars(select(AIComparisonCompetitor)).all() == []


def test_rerun_creates_new_analysis_without_overwriting_completed_result(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    first_execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    second_execution, _, _ = make_execution(db, run, "Beta", "beta.example", Decimal("49"))

    first = execute_ai_analysis(
        db,
        run.id,
        provider=FakeProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )
    second = execute_ai_analysis(
        db,
        run.id,
        provider=FakeProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )

    assert first.status == "completed"
    assert second.status == "completed"
    assert first.id != second.id
    assert db.scalars(select(AIAnalysis).where(AIAnalysis.research_run_id == run.id)).all() == [first, second]


def test_execute_ai_analysis_marks_failed_when_provider_raises(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    competitor = Competitor(research_run_id=run.id, name="Alpha", domain="alpha.example")
    db.add(competitor)
    db.flush()
    execution = CompetitorResearch(competitor_id=competitor.id, research_run_id=run.id)
    db.add(execution)
    db.flush()
    for section_name in (
        "company_overview",
        "products",
        "features",
        "pricing",
        "target_audience",
        "customer_feedback",
    ):
        db.add(CompetitorResearchSection(competitor_research_id=execution.id, section=section_name))
    db.commit()

    class FailingProvider:
        def analyze(self, context):
            raise ProviderUnavailableError("Gemini is unavailable")

    analysis = execute_ai_analysis(
        db,
        run.id,
        provider=FailingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )

    assert analysis.status == "failed"
    assert "Gemini is unavailable" in analysis.failure_reason

from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
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
from app.services import ai_analysis as ai_analysis_service


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class FakeProvider:
    provider_name = "fake-provider"
    model_name = "fake-model"

    def analyze(self, context):
        return ProviderAnalysisResult(
            scope=context.scope,
            provider="fake-provider",
            model="fake-model",
            statements=[
                AIStatementResult(
                    statement_id="STATEMENT_001",
                    statement_type="observation",
                    section="features",
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
            ] if len(context.competitors) > 1 else [],
        )


class CountingProvider(FakeProvider):
    def __init__(self, provider_name="fake-provider", model_name="fake-model"):
        self.calls = 0
        self.provider_name = provider_name
        self.model_name = model_name

    def analyze(self, context):
        self.calls += 1
        return super().analyze(context)


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
    assert analysis.statements[0].section == "features"
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
        provider_name = "recording-provider"
        model_name = "recording-model"

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


def test_rerun_reuses_completed_analysis(db: Session):
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
    assert first.id == second.id
    assert db.scalars(select(AIAnalysis).where(AIAnalysis.research_run_id == run.id)).all() == [first]


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
        provider_name = "failing-provider"
        model_name = "failing-model"

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
    retry = execute_ai_analysis(
        db,
        run.id,
        provider=FailingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )
    assert retry.status == "failed"
    assert retry.id != analysis.id
    assert retry.request_fingerprint == analysis.request_fingerprint


def test_pending_and_running_analysis_are_reused(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    provider = CountingProvider()

    first = execute_ai_analysis(
        db,
        run.id,
        provider=provider,
        scope="competitor",
        competitor_research_id=execution.id,
    )
    first.status = "pending"
    db.commit()
    pending = execute_ai_analysis(
        db,
        run.id,
        provider=provider,
        scope="competitor",
        competitor_research_id=execution.id,
    )
    assert pending.id == first.id

    first.status = "running"
    db.commit()
    running = execute_ai_analysis(
        db,
        run.id,
        provider=provider,
        scope="competitor",
        competitor_research_id=execution.id,
    )
    assert running.id == first.id
    assert provider.calls == 1


def test_reordered_ids_reuse_and_changed_identity_inputs_do_not(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    first_execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    second_execution, _, _ = make_execution(db, run, "Beta", "beta.example", Decimal("49"))

    first = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )
    reordered = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="research_run",
        competitor_research_ids=[second_execution.id, first_execution.id],
    )
    changed_ids = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="competitor",
        competitor_research_id=first_execution.id,
    )
    changed_prompt = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
        prompt_version="prompt-v2",
    )
    changed_contract = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
        contract_version="contract-v2",
    )
    changed_provider = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(provider_name="other-provider"),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )
    changed_model = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(model_name="other-model"),
        scope="research_run",
        competitor_research_ids=[first_execution.id, second_execution.id],
    )

    assert reordered.id == first.id
    assert changed_ids.id != first.id
    assert changed_prompt.id != first.id
    assert changed_contract.id != first.id
    assert changed_provider.id != first.id
    assert changed_model.id != first.id


def test_changed_snapshot_creates_new_fingerprint(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, fact, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    first = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )
    fact.value_numeric = Decimal("39")
    db.commit()
    second = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )
    assert second.id != first.id
    assert second.request_fingerprint != first.request_fingerprint


def test_identical_request_does_not_call_provider_twice(db: Session):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    provider = CountingProvider()
    first = execute_ai_analysis(
        db, run.id, provider=provider, scope="competitor", competitor_research_id=execution.id
    )
    second = execute_ai_analysis(
        db, run.id, provider=provider, scope="competitor", competitor_research_id=execution.id
    )
    assert second.id == first.id
    assert provider.calls == 1


def test_unique_insert_race_reuses_winner_and_preserves_outer_work(db: Session, monkeypatch):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    winner = execute_ai_analysis(
        db,
        run.id,
        provider=CountingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )
    unrelated = ResearchRun(input_value="Unrelated work")
    db.add(unrelated)
    db.flush()
    research_run_id = run.id
    unrelated_id = unrelated.id

    lookup_results = iter((None, winner))
    monkeypatch.setattr(
        ai_analysis_service.ai_analysis_repository,
        "get_reusable_by_request_fingerprint",
        lambda *args, **kwargs: next(lookup_results),
    )
    original_flush = db.flush

    def raise_unique(*args, **kwargs):
        if any(
            isinstance(item, AIAnalysis) and item.request_fingerprint is not None
            for item in db.new
        ):
            raise IntegrityError("duplicate fingerprint", {}, Exception("duplicate"))
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", raise_unique)
    reused = execute_ai_analysis(
        db,
        research_run_id,
        provider=CountingProvider(),
        scope="competitor",
        competitor_research_id=execution.id,
    )
    assert reused.id == winner.id

    monkeypatch.setattr(db, "flush", original_flush)
    db.commit()
    assert db.get(ResearchRun, unrelated_id) is not None


def test_unrelated_integrity_error_is_reraised(db: Session, monkeypatch):
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))
    research_run_id = run.id

    monkeypatch.setattr(
        ai_analysis_service.ai_analysis_repository,
        "get_reusable_by_request_fingerprint",
        lambda *args, **kwargs: None,
    )

    def raise_integrity(*args, **kwargs):
        if any(
            isinstance(item, AIAnalysis) and item.request_fingerprint is not None
            for item in db.new
        ):
            raise IntegrityError("unrelated constraint", {}, Exception("unrelated"))
        return original_flush(*args, **kwargs)

    original_flush = db.flush
    monkeypatch.setattr(db, "flush", raise_integrity)
    with pytest.raises(IntegrityError, match="unrelated constraint"):
        execute_ai_analysis(
            db,
            research_run_id,
            provider=CountingProvider(),
            scope="competitor",
            competitor_research_id=execution.id,
        )


def test_provider_without_model_identity_fails_before_persistence(db: Session):
    class UnidentifiedProvider:
        provider_name = "unidentified-provider"

        def analyze(self, context):
            raise AssertionError("provider must not be called")

    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    execution, _, _ = make_execution(db, run, "Alpha", "alpha.example", Decimal("29"))

    with pytest.raises(ValueError, match="configured model identity"):
        execute_ai_analysis(
            db,
            run.id,
            provider=UnidentifiedProvider(),
            scope="competitor",
            competitor_research_id=execution.id,
        )

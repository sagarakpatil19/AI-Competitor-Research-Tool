from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.context.analysis_context import AnalysisContextRequest
from app.context.analysis_context_builder import AnalysisContextBuilder, AnalysisContextError, build_analysis_context
from app.db.base import Base
from app.models import (
    Competitor,
    CompetitorEvidence,
    CompetitorResearch,
    CompetitorResearchFact,
    CompetitorResearchFactEvidence,
    CompetitorResearchSection,
    CompetitorSource,
    ResearchRun,
)


SECTION_NAMES = (
    "company_overview",
    "products",
    "features",
    "pricing",
    "target_audience",
    "customer_feedback",
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def create_execution(db: Session, name: str, domain: str) -> tuple[ResearchRun, Competitor, CompetitorResearch]:
    run = ResearchRun(input_value="Acme")
    db.add(run)
    db.flush()
    competitor = Competitor(research_run_id=run.id, name=name, domain=domain)
    db.add(competitor)
    db.flush()
    execution = CompetitorResearch(competitor_id=competitor.id, research_run_id=run.id)
    db.add(execution)
    db.flush()
    for section_name in SECTION_NAMES:
        db.add(CompetitorResearchSection(competitor_research_id=execution.id, section=section_name))
    db.flush()
    return run, competitor, execution


def add_fact_and_evidence(
    db: Session,
    execution: CompetitorResearch,
    *,
    amount: Decimal = Decimal("29"),
    source: bool = False,
) -> tuple[CompetitorResearchFact, CompetitorEvidence]:
    source_row = None
    if source:
        source_row = CompetitorSource(
            competitor_research_id=execution.id,
            canonical_url="https://example.com/pricing",
            source_type="pricing",
            discovery_method="manual",
            status="collected",
        )
        db.add(source_row)
        db.flush()
    evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_id=source_row.id if source_row else None,
        source_url="https://example.com/pricing",
        source_title="Pricing",
        source_type="pricing",
        content="Plans start at $29 per month.",
        normalized_content="Plans start at $29 per month.",
        normalized_excerpt="Plans start at $29 per month.",
        normalized_content_hash="a" * 64,
        processing_status="processed",
        validation_status="valid",
    )
    fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="pricing",
        fact_type="starting_price",
        value_numeric=amount,
        currency="USD",
        unit="month",
        normalized_key=f"pricing:starting_price:month:{amount}",
    )
    db.add_all([fact, evidence])
    db.flush()
    db.add(CompetitorResearchFactEvidence(fact_id=fact.id, evidence_id=evidence.id))
    db.commit()
    return fact, evidence


def request(scope: str, run_id: int, execution_id: int | None = None, execution_ids: list[int] | None = None):
    return AnalysisContextRequest(
        scope=scope,
        research_run_id=run_id,
        competitor_research_id=execution_id,
        competitor_research_ids=execution_ids or [],
        contract_version="contract-v1",
        prompt_version="prompt-v1",
    )


def test_competitor_context_is_explicit_and_preserves_provenance(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    fact, evidence = add_fact_and_evidence(db, execution, source=True)

    result = build_analysis_context(db, request("competitor", run.id, execution.id))
    context = result.context

    assert [item.context_id for item in context.competitors] == ["COMPETITOR_001"]
    assert context.facts[0].context_id == "FACT_001"
    assert context.facts[0].evidence_context_ids == ["EVIDENCE_001"]
    assert context.evidence[0].source_context_id == "SOURCE_001"
    assert result.mapping.fact_context_to_database_id == {"FACT_001": fact.id}
    assert result.mapping.evidence_context_to_database_id == {"EVIDENCE_001": evidence.id}
    assert result.mapping.database_fact_to_context_id == {fact.id: "FACT_001"}
    assert result.mapping.database_evidence_to_context_id == {evidence.id: "EVIDENCE_001"}
    assert context.facts[0].value_numeric == Decimal("29")


def test_research_run_context_uses_multiple_explicit_executions_deterministically(db: Session):
    run, _, first = create_execution(db, "Zeta", "zeta.example")
    second_competitor = Competitor(research_run_id=run.id, name="Alpha", domain="alpha.example")
    db.add(second_competitor)
    db.flush()
    second = CompetitorResearch(competitor_id=second_competitor.id, research_run_id=run.id)
    db.add(second)
    db.flush()
    for section_name in SECTION_NAMES:
        db.add(CompetitorResearchSection(competitor_research_id=second.id, section=section_name))
    db.commit()
    add_fact_and_evidence(db, first, amount=Decimal("49"))
    add_fact_and_evidence(db, second, amount=Decimal("29"))

    context = build_analysis_context(db, request("research_run", run.id, execution_ids=[first.id, second.id])).context

    assert [item.name for item in context.competitors] == ["Alpha", "Zeta"]
    assert [item.context_id for item in context.competitors] == ["COMPETITOR_001", "COMPETITOR_002"]
    assert [fact.value_numeric for fact in context.facts] == [Decimal("29"), Decimal("49")]


def test_valid_evidence_without_fact_is_included_and_invalid_states_are_excluded(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution)
    db.add_all([
        CompetitorEvidence(
            competitor_research_id=execution.id,
            source_url="https://example.com/invalid",
            content="invalid",
            normalized_content="invalid",
            processing_status="processed",
            validation_status="invalid",
        ),
        CompetitorEvidence(
            competitor_research_id=execution.id,
            source_url="https://example.com/pending",
            content="pending",
            processing_status="pending",
            validation_status="pending",
        ),
        CompetitorEvidence(
            competitor_research_id=execution.id,
            source_url="https://example.com/unfactored",
            content="Valid evidence with no deterministic fact.",
            normalized_content="Valid evidence with no deterministic fact.",
            normalized_content_hash="b" * 64,
            processing_status="processed",
            validation_status="valid",
        ),
    ])
    db.commit()

    context = build_analysis_context(db, request("competitor", run.id, execution.id)).context

    assert len(context.evidence) == 2
    assert any(not evidence.fact_context_ids for evidence in context.evidence)
    assert context.sections[3].valid_evidence_count == 2


def test_conflicting_facts_are_preserved_and_hash_is_deterministic(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution, amount=Decimal("29"))
    second_fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="pricing",
        fact_type="starting_price",
        value_numeric=49,
        currency="USD",
        unit="month",
        normalized_key="pricing:starting_price:month:49",
    )
    second_evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_url="https://example.com/pricing-2",
        normalized_content="Plans start at $49 per month.",
        normalized_content_hash="c" * 64,
        processing_status="processed",
        validation_status="valid",
    )
    db.add_all([second_fact, second_evidence])
    db.flush()
    db.add(CompetitorResearchFactEvidence(fact_id=second_fact.id, evidence_id=second_evidence.id))
    db.commit()

    first = build_analysis_context(db, request("competitor", run.id, execution.id)).context
    second = build_analysis_context(db, request("competitor", run.id, execution.id)).context

    assert [fact.value_numeric for fact in first.facts] == [Decimal("29"), Decimal("49")]
    assert first.snapshot.input_snapshot_hash == second.snapshot.input_snapshot_hash
    assert first.snapshot.generated_at != second.snapshot.generated_at


def test_evidence_linked_to_multiple_facts_is_included_once(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    first_fact, evidence = add_fact_and_evidence(db, execution)
    second_fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="pricing",
        fact_type="price",
        value_numeric=29,
        currency="USD",
        unit="month",
        normalized_key="pricing:price:month:29",
    )
    db.add(second_fact)
    db.flush()
    db.add(CompetitorResearchFactEvidence(fact_id=second_fact.id, evidence_id=evidence.id))
    db.commit()

    context = build_analysis_context(db, request("competitor", run.id, execution.id)).context

    assert len(context.evidence) == 1
    assert context.evidence[0].fact_context_ids == ["FACT_001", "FACT_002"]


def test_provider_context_excludes_mapping_and_database_ids(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution, source=True)

    result = build_analysis_context(db, request("competitor", run.id, execution.id))
    serialized = result.context.model_dump()

    assert "mapping" not in serialized
    assert "research_run_id" not in serialized
    serialized_text = str(serialized)
    assert "competitor_research_id" not in serialized_text
    assert "database_fact_id" not in serialized_text
    assert "database_evidence_id" not in serialized_text
    assert "database_source_id" not in serialized_text
    assert result.mapping.database_competitor_to_context_id
    assert result.mapping.database_source_to_context_id


def test_reverse_mappings_round_trip_for_all_selected_entities(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    fact, evidence = add_fact_and_evidence(db, execution, source=True)

    result = build_analysis_context(db, request("competitor", run.id, execution.id))
    mapping = result.mapping

    for forward, reverse in (
        (mapping.competitor_context_to_database_id, mapping.database_competitor_to_context_id),
        (mapping.fact_context_to_database_id, mapping.database_fact_to_context_id),
        (mapping.evidence_context_to_database_id, mapping.database_evidence_to_context_id),
        (mapping.source_context_to_database_id, mapping.database_source_to_context_id),
    ):
        assert len(forward) == len(reverse)
        assert all(reverse[database_id] == context_id for context_id, database_id in forward.items())

    assert mapping.database_fact_to_context_id[fact.id] == "FACT_001"
    assert mapping.database_evidence_to_context_id[evidence.id] == "EVIDENCE_001"


def test_included_content_and_fact_value_change_snapshot_hash(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    fact, evidence = add_fact_and_evidence(db, execution)
    before_content = build_analysis_context(db, request("competitor", run.id, execution.id)).context.snapshot.input_snapshot_hash

    evidence.normalized_content = "Plans start at $30 per month."
    db.commit()
    after_content = build_analysis_context(db, request("competitor", run.id, execution.id)).context.snapshot.input_snapshot_hash
    assert before_content != after_content

    evidence.normalized_content = "Plans start at $29 per month."
    fact.value_numeric = Decimal("30")
    db.commit()
    after_fact = build_analysis_context(db, request("competitor", run.id, execution.id)).context.snapshot.input_snapshot_hash
    assert after_content != after_fact


def test_equivalent_datetime_offsets_have_same_canonical_hash(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution)
    first = build_analysis_context(db, request("competitor", run.id, execution.id)).context
    second_evidence = first.evidence[0].model_copy(
        update={"retrieved_at": datetime(2026, 9, 21, 10, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))}
    )
    first_evidence = first.evidence[0].model_copy(
        update={"retrieved_at": datetime(2026, 9, 21, 4, 30, tzinfo=timezone.utc)}
    )
    builder = AnalysisContextBuilder(db)
    first_payload = builder._snapshot_payload(
        request("competitor", run.id, execution.id),
        first.competitors,
        first.sections,
        first.facts,
        [first_evidence],
        first.sources,
    )
    second_payload = builder._snapshot_payload(
        request("competitor", run.id, execution.id),
        first.competitors,
        first.sections,
        first.facts,
        [second_evidence],
        first.sources,
    )
    first_hash = __import__("hashlib").sha256(
        __import__("json").dumps(first_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    second_hash = __import__("hashlib").sha256(
        __import__("json").dumps(second_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert first_hash == second_hash


def test_generated_at_is_excluded_from_snapshot_hash(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution)
    first = build_analysis_context(db, request("competitor", run.id, execution.id)).context
    second = first.model_copy(update={"snapshot": first.snapshot.model_copy(update={
        "generated_at": datetime(2030, 1, 1, tzinfo=timezone.utc),
    })})
    assert first.snapshot.input_snapshot_hash == second.snapshot.input_snapshot_hash


def test_invalid_cross_execution_fact_evidence_association_fails_closed(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    _, _, other_execution = create_execution(db, "Other", "other.example")
    fact, evidence = add_fact_and_evidence(db, execution)
    other_evidence = CompetitorEvidence(
        competitor_research_id=other_execution.id,
        source_url="https://other.example/evidence",
        normalized_content="Other execution evidence.",
        processing_status="processed",
        validation_status="valid",
    )
    db.add(other_evidence)
    db.flush()
    db.add(CompetitorResearchFactEvidence(fact_id=fact.id, evidence_id=other_evidence.id))
    db.commit()

    with pytest.raises(AnalysisContextError, match="crosses executions|missing evidence"):
        build_analysis_context(db, request("competitor", run.id, execution.id))


def test_cross_execution_source_relationship_is_rejected(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    _, _, other_execution = create_execution(db, "Other", "other.example")
    source = CompetitorSource(
        competitor_research_id=other_execution.id,
        canonical_url="https://other.example/source",
    )
    db.add(source)
    db.flush()
    db.add(CompetitorEvidence(
        competitor_research_id=execution.id,
        source_id=source.id,
        source_url=source.canonical_url,
        normalized_content="Valid evidence with an invalid source relationship.",
        processing_status="processed",
        validation_status="valid",
    ))
    db.commit()

    with pytest.raises(AnalysisContextError, match="source relationship is invalid"):
        build_analysis_context(db, request("competitor", run.id, execution.id))


def test_contract_and_prompt_versions_change_snapshot_hash(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    add_fact_and_evidence(db, execution)

    baseline = build_analysis_context(db, request("competitor", run.id, execution.id)).context
    contract_changed = build_analysis_context(
        db,
        AnalysisContextRequest(
            scope="competitor",
            research_run_id=run.id,
            competitor_research_id=execution.id,
            contract_version="contract-v2",
            prompt_version="prompt-v1",
        ),
    ).context
    prompt_changed = build_analysis_context(
        db,
        AnalysisContextRequest(
            scope="competitor",
            research_run_id=run.id,
            competitor_research_id=execution.id,
            contract_version="contract-v1",
            prompt_version="prompt-v2",
        ),
    ).context

    assert baseline.snapshot.input_snapshot_hash != contract_changed.snapshot.input_snapshot_hash
    assert baseline.snapshot.input_snapshot_hash != prompt_changed.snapshot.input_snapshot_hash


def test_scope_and_ownership_validation_rejects_ambiguous_or_cross_run_requests(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    other_run, _, other_execution = create_execution(db, "Other", "other.example")

    with pytest.raises(ValidationError):
        request("research_run", run.id)
    with pytest.raises(ValidationError):
        request("competitor", run.id, execution.id, [execution.id])
    with pytest.raises(ValidationError):
        request("research_run", run.id, execution_id=execution.id, execution_ids=[execution.id])
    with pytest.raises(ValidationError):
        request("research_run", run.id, execution_ids=[execution.id, execution.id])
    with pytest.raises(AnalysisContextError):
        build_analysis_context(db, request("competitor", run.id, other_execution.id))
    assert other_run.id != run.id


def test_missing_section_is_malformed_and_builder_is_read_only(db: Session):
    run, _, execution = create_execution(db, "Acme", "acme.example")
    db.query(CompetitorResearchSection).filter_by(
        competitor_research_id=execution.id,
        section="pricing",
    ).delete()
    db.commit()
    before = db.scalar(select(CompetitorResearchFact).where(CompetitorResearchFact.competitor_research_id == execution.id))

    with pytest.raises(AnalysisContextError, match="all six sections"):
        build_analysis_context(db, request("competitor", run.id, execution.id))

    after = db.scalar(select(CompetitorResearchFact).where(CompetitorResearchFact.competitor_research_id == execution.id))
    assert before == after

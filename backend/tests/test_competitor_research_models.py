import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Competitor,
    CompetitorEvidence,
    CompetitorResearch,
    CompetitorResearchFact,
    CompetitorResearchFactEvidence,
    CompetitorResearchSection,
    ResearchRun,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def create_execution(db: Session, name: str = "Acme") -> tuple[ResearchRun, Competitor, CompetitorResearch]:
    research_run = ResearchRun(input_value=name)
    db.add(research_run)
    db.flush()
    competitor = Competitor(research_run_id=research_run.id, name=name, domain="acme.example")
    db.add(competitor)
    db.flush()
    execution = CompetitorResearch(
        competitor_id=competitor.id,
        research_run_id=research_run.id,
    )
    db.add(execution)
    db.flush()
    return research_run, competitor, execution


def test_multiple_historical_executions_can_belong_to_one_competitor(db: Session):
    research_run, competitor, first = create_execution(db)
    second = CompetitorResearch(
        competitor_id=competitor.id,
        research_run_id=research_run.id,
    )
    db.add(second)
    db.commit()

    assert [execution.id for execution in competitor.research_executions] == [first.id, second.id]
    assert first.research_run_id == research_run.id
    assert second.research_run_id == research_run.id


def test_fact_and_fact_evidence_preserve_execution_provenance(db: Session):
    research_run, competitor, execution = create_execution(db)
    evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_url="https://acme.example/about",
        content="Acme provides collaboration software for distributed teams.",
    )
    fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="company_overview",
        fact_type="description",
        subject="Acme",
        value_text="Acme provides collaboration software for distributed teams.",
        normalized_key="company_overview:description:acme",
    )
    db.add_all([evidence, fact])
    db.flush()
    association = CompetitorResearchFactEvidence(
        fact_id=fact.id,
        evidence_id=evidence.id,
        citation_excerpt="Acme provides collaboration software for distributed teams.",
    )
    db.add(association)
    db.commit()

    assert fact.competitor_research.id == execution.id
    assert fact.evidence_links[0].evidence.competitor_research_id == execution.id
    assert association.fact_id == fact.id
    assert association.evidence_id == evidence.id
    assert competitor.research_run_id == research_run.id


def test_duplicate_fact_evidence_association_is_rejected(db: Session):
    _, _, execution = create_execution(db)
    evidence = CompetitorEvidence(
        competitor_research_id=execution.id,
        source_url="https://acme.example/about",
        content="Acme provides collaboration software for distributed teams.",
    )
    fact = CompetitorResearchFact(
        competitor_research_id=execution.id,
        section="company_overview",
        fact_type="description",
        value_text="Acme provides collaboration software for distributed teams.",
        normalized_key="company_overview:description:acme",
    )
    db.add_all([evidence, fact])
    db.flush()
    db.add(CompetitorResearchFactEvidence(fact_id=fact.id, evidence_id=evidence.id))
    db.commit()

    db.add(CompetitorResearchFactEvidence(fact_id=fact.id, evidence_id=evidence.id))
    with pytest.raises(IntegrityError):
        db.commit()


def test_section_is_unique_per_execution(db: Session):
    _, _, execution = create_execution(db)
    db.add_all(
        [
            CompetitorResearchSection(
                competitor_research_id=execution.id,
                section="pricing",
            ),
            CompetitorResearchSection(
                competitor_research_id=execution.id,
                section="pricing",
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_invalid_status_and_section_values_are_rejected(db: Session):
    _, _, execution = create_execution(db)
    execution.status = "unknown"
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    execution.status = "pending"
    db.add(
        CompetitorResearchSection(
            competitor_research_id=execution.id,
            section="sources",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_sources_is_not_a_valid_fact_section(db: Session):
    _, _, execution = create_execution(db)
    db.add(
        CompetitorResearchFact(
            competitor_research_id=execution.id,
            section="sources",
            fact_type="source",
            normalized_key="sources:source:example",
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_historical_execution_facts_are_not_overwritten(db: Session):
    research_run, competitor, first = create_execution(db)
    second = CompetitorResearch(
        competitor_id=competitor.id,
        research_run_id=research_run.id,
    )
    db.add(second)
    db.flush()
    db.add_all(
        [
            CompetitorResearchFact(
                competitor_research_id=first.id,
                section="pricing",
                fact_type="starting_price",
                value_numeric=10,
                currency="USD",
                normalized_key="pricing:starting_price:10",
            ),
            CompetitorResearchFact(
                competitor_research_id=second.id,
                section="pricing",
                fact_type="starting_price",
                value_numeric=20,
                currency="USD",
                normalized_key="pricing:starting_price:20",
            ),
        ]
    )
    db.commit()

    assert db.query(CompetitorResearchFact).filter_by(competitor_research_id=first.id).count() == 1
    assert db.query(CompetitorResearchFact).filter_by(competitor_research_id=second.id).count() == 1

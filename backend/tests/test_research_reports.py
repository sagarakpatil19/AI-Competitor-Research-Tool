import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.base import Base
from app.models import (
    AIAnalysis,
    AIComparison,
    AIStatement,
    ResearchRun,
    ResearchReport,
    ResearchReportSection,
    ResearchReportSectionItem,
    Competitor,
    CompetitorResearch,
)
from app.schemas.research_report import (
    ResearchReportCreate,
    ResearchReportSectionCreate,
    ResearchReportSectionItemCreate,
)
from app.services.research_reports import (
    create_report,
    create_report_section,
    create_report_section_item,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def make_analysis(
    db: Session,
    *,
    run: ResearchRun,
    scope: str = "research_run",
    status: str = "completed",
    competitor_research_id: int | None = None,
) -> AIAnalysis:
    analysis = AIAnalysis(
        research_run_id=run.id,
        competitor_research_id=competitor_research_id,
        scope=scope,
        status=status,
        provider_name="fake-provider",
        model_name="fake-model",
        prompt_version="prompt-v1",
        contract_version="contract-v1",
    )
    db.add(analysis)
    db.flush()
    return analysis


def make_report_context(db: Session):
    first_run = ResearchRun(input_value="Acme")
    second_run = ResearchRun(input_value="Beta")
    db.add_all([first_run, second_run])
    db.flush()
    first_analysis = make_analysis(db, run=first_run)
    second_analysis = make_analysis(db, run=second_run)
    competitor = Competitor(research_run_id=first_run.id, name="Acme competitor", domain="competitor.example")
    db.add(competitor)
    db.flush()
    competitor_execution = CompetitorResearch(
        competitor_id=competitor.id,
        research_run_id=first_run.id,
    )
    db.add(competitor_execution)
    db.flush()
    competitor_analysis = make_analysis(
        db,
        run=first_run,
        scope="competitor",
        competitor_research_id=competitor_execution.id,
    )
    failed_analysis = make_analysis(db, run=first_run, status="failed")
    pending_analysis = make_analysis(db, run=first_run, status="pending")
    first_statement = AIStatement(
        analysis_id=first_analysis.id,
        statement_type="observation",
        text="Acme has a supported pricing observation.",
        support_status="supported",
    )
    second_statement = AIStatement(
        analysis_id=second_analysis.id,
        statement_type="observation",
        text="Beta has a supported pricing observation.",
        support_status="supported",
    )
    first_comparison = AIComparison(
        analysis_id=first_analysis.id,
        comparison_type="pricing",
        dimension="starting_price",
        statement="Acme pricing comparison.",
        support_status="supported",
    )
    second_comparison = AIComparison(
        analysis_id=second_analysis.id,
        comparison_type="pricing",
        dimension="starting_price",
        statement="Beta pricing comparison.",
        support_status="supported",
    )
    db.add_all([first_statement, second_statement, first_comparison, second_comparison])
    db.commit()
    return {
        "first_run": first_run,
        "second_run": second_run,
        "first_analysis": first_analysis,
        "second_analysis": second_analysis,
        "competitor_analysis": competitor_analysis,
        "failed_analysis": failed_analysis,
        "pending_analysis": pending_analysis,
        "first_statement": first_statement,
        "second_statement": second_statement,
        "first_comparison": first_comparison,
        "second_comparison": second_comparison,
    }


def create_first_report(db: Session, context):
    return create_report(
        db,
        ResearchReportCreate(
            research_run_id=context["first_run"].id,
            analysis_id=context["first_analysis"].id,
        ),
    )


def test_report_creation_requires_completed_research_run_analysis(db: Session):
    context = make_report_context(db)
    report = create_first_report(db, context)

    assert report.status == "pending"
    assert report.version == 1
    assert report.research_run_id == context["first_run"].id
    assert report.analysis_id == context["first_analysis"].id

    for key in ("competitor_analysis", "failed_analysis", "pending_analysis"):
        with pytest.raises(ValueError):
            create_report(
                db,
                ResearchReportCreate(
                    research_run_id=context["first_run"].id,
                    analysis_id=context[key].id,
                ),
            )


def test_report_rejects_cross_run_analysis_and_preserves_history(db: Session):
    context = make_report_context(db)
    first = create_first_report(db, context)

    with pytest.raises(ValueError, match="belong to the research run"):
        create_report(
            db,
            ResearchReportCreate(
                research_run_id=context["first_run"].id,
                analysis_id=context["second_analysis"].id,
            ),
        )

    second = create_first_report(db, context)
    assert first.id != second.id
    assert first.version == 1
    assert second.version == 2
    assert db.scalars(select(ResearchReport).where(ResearchReport.research_run_id == context["first_run"].id)).all() == [first, second]


def test_sections_and_items_preserve_m12_references_and_validate_ownership(db: Session):
    context = make_report_context(db)
    report = create_first_report(db, context)
    section = create_report_section(
        db,
        ResearchReportSectionCreate(
            report_id=report.id,
            section="key_findings",
            status="pending",
            display_order=0,
        ),
    )

    statement_item = create_report_section_item(
        db,
        ResearchReportSectionItemCreate(
            section_id=section.id,
            item_type="statement",
            ai_statement_id=context["first_statement"].id,
            display_order=0,
        ),
    )
    comparison_item = create_report_section_item(
        db,
        ResearchReportSectionItemCreate(
            section_id=section.id,
            item_type="comparison",
            ai_comparison_id=context["first_comparison"].id,
            display_order=1,
        ),
    )

    assert statement_item.ai_statement_id == context["first_statement"].id
    assert statement_item.ai_comparison_id is None
    assert comparison_item.ai_comparison_id == context["first_comparison"].id
    assert comparison_item.ai_statement_id is None

    with pytest.raises(ValueError, match="statement"):
        create_report_section_item(
            db,
            ResearchReportSectionItemCreate(
                section_id=section.id,
                item_type="statement",
                ai_statement_id=context["second_statement"].id,
                display_order=2,
            ),
        )
    with pytest.raises(ValueError, match="comparison"):
        create_report_section_item(
            db,
            ResearchReportSectionItemCreate(
                section_id=section.id,
                item_type="comparison",
                ai_comparison_id=context["second_comparison"].id,
                display_order=3,
            ),
        )


def test_item_contract_rejects_invalid_reference_shape_and_type():
    with pytest.raises(ValidationError):
        ResearchReportSectionItemCreate(
            section_id=1,
            item_type="statement",
            ai_statement_id=1,
            ai_comparison_id=2,
            display_order=0,
        )
    with pytest.raises(ValidationError):
        ResearchReportSectionItemCreate(
            section_id=1,
            item_type="comparison",
            display_order=0,
        )
    with pytest.raises(ValidationError):
        ResearchReportSectionItemCreate(
            section_id=1,
            item_type="invalid",
            display_order=0,
        )


def test_model_constraints_cover_statuses_and_exact_item_reference(db: Session):
    context = make_report_context(db)
    report = ResearchReport(
        research_run_id=context["first_run"].id,
        analysis_id=context["first_analysis"].id,
        status="invalid",
        version=1,
    )
    db.add(report)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    report = create_first_report(db, context)
    section = ResearchReportSection(
        report_id=report.id,
        section="key_findings",
        status="invalid",
        display_order=0,
    )
    db.add(section)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    section = create_report_section(
        db,
        ResearchReportSectionCreate(report_id=report.id, section="key_findings", display_order=0),
    )
    db.add(
        ResearchReportSectionItem(
            section_id=section.id,
            item_type="statement",
            ai_statement_id=context["first_statement"].id,
            ai_comparison_id=context["first_comparison"].id,
            display_order=0,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_report_metadata_and_migration_tables_are_present(db: Session):
    tables = set(inspect(db.bind).get_table_names())
    assert {
        "research_reports",
        "research_report_sections",
        "research_report_section_items",
    } <= tables
    assert "uq_research_reports_run_version" in {
        constraint["name"]
        for constraint in inspect(db.bind).get_unique_constraints("research_reports")
    }

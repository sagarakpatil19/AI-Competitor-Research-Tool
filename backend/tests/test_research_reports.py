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
    REPORT_SECTIONS,
    compose_report,
    create_report,
    create_report_section,
    create_report_section_item,
    generate_report,
)
from app.services import research_reports as research_reports_service


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


def test_compose_report_creates_all_sections_and_preserves_m12_references(db: Session):
    context = make_report_context(db)
    context["first_statement"].section = "pricing"
    null_section_statement = AIStatement(
        analysis_id=context["first_analysis"].id,
        statement_type="observation",
        text="Unsectioned finding.",
        support_status="supported",
    )
    unmapped_statement = AIStatement(
        analysis_id=context["first_analysis"].id,
        statement_type="observation",
        text="Unsupported section finding.",
        support_status="supported",
        section="not_a_report_section",
    )
    db.add_all([null_section_statement, unmapped_statement])
    db.commit()
    report = create_first_report(db, context)

    composed = compose_report(db, report.id)

    assert composed.status == "completed"
    assert [section.section for section in composed.sections] == list(REPORT_SECTIONS)
    sections = {section.section: section for section in composed.sections}
    assert sections["pricing"].status == "completed"
    assert sections["comparisons"].status == "completed"
    assert sections["key_findings"].status == "no_content"
    assert sections["company_overview"].status == "no_content"
    assert [item.ai_statement_id for item in sections["pricing"].items] == [context["first_statement"].id]
    assert [item.ai_comparison_id for item in sections["comparisons"].items] == [context["first_comparison"].id]
    assert all(item.ai_statement_id != null_section_statement.id for item in sections["pricing"].items)
    assert all(item.ai_statement_id != unmapped_statement.id for item in sections["pricing"].items)


def test_compose_report_orders_statements_and_comparisons_deterministically(db: Session):
    context = make_report_context(db)
    first_statement = context["first_statement"]
    first_statement.section = "products"
    second_statement = AIStatement(
        analysis_id=context["first_analysis"].id,
        statement_type="observation",
        text="Later finding.",
        support_status="supported",
        section="products",
    )
    second_comparison = AIComparison(
        analysis_id=context["first_analysis"].id,
        comparison_type="features",
        dimension="feature",
        statement="Later comparison.",
        support_status="supported",
    )
    db.add_all([second_statement, second_comparison])
    db.commit()
    report = create_first_report(db, context)

    composed = compose_report(db, report.id)
    sections = {section.section: section for section in composed.sections}

    assert [item.ai_statement_id for item in sections["products"].items] == [first_statement.id, second_statement.id]
    assert [item.ai_comparison_id for item in sections["comparisons"].items] == [context["first_comparison"].id, second_comparison.id]
    assert [section.display_order for section in composed.sections] == list(range(8))


def test_compose_report_rejects_recomposition_and_does_not_duplicate_items(db: Session):
    context = make_report_context(db)
    context["first_statement"].section = "pricing"
    db.commit()
    report = create_first_report(db, context)
    compose_report(db, report.id)
    item_count = db.query(ResearchReportSectionItem).count()

    with pytest.raises(ValueError, match="Only pending"):
        compose_report(db, report.id)

    assert db.query(ResearchReportSectionItem).count() == item_count


def test_compose_report_returns_failed_report_without_partial_sections_on_failure(db: Session, monkeypatch):
    context = make_report_context(db)
    report = create_first_report(db, context)
    original_flush = db.flush
    flush_count = 0

    def fail_after_sections(*args, **kwargs):
        nonlocal flush_count
        flush_count += 1
        if flush_count == 2:
            raise RuntimeError("section composition failed")
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(db, "flush", fail_after_sections)

    failed = compose_report(db, report.id)

    assert failed.status == "failed"
    assert "section composition failed" in failed.failure_reason
    assert db.query(ResearchReportSection).filter_by(report_id=report.id).count() == 0
    assert db.query(ResearchReportSectionItem).count() == 0


def test_compose_report_rejects_invalid_analysis_ownership_and_status(db: Session):
    context = make_report_context(db)
    cross_run_report = ResearchReport(
        research_run_id=context["first_run"].id,
        analysis_id=context["second_analysis"].id,
        status="pending",
        version=99,
    )
    db.add(cross_run_report)
    db.commit()

    with pytest.raises(ValueError, match="belong to the report research run"):
        compose_report(db, cross_run_report.id)
    assert db.get(ResearchReport, cross_run_report.id).status == "pending"

    for version, key in enumerate(("competitor_analysis", "failed_analysis", "pending_analysis"), start=100):
        report = ResearchReport(
            research_run_id=context["first_run"].id,
            analysis_id=context[key].id,
            status="pending",
            version=version,
        )
        db.add(report)
        db.commit()
        with pytest.raises(ValueError):
            compose_report(db, report.id)
        assert db.get(ResearchReport, report.id).status == "pending"


def test_generate_report_composes_the_explicit_completed_analysis(db: Session):
    context = make_report_context(db)
    context["first_statement"].section = "pricing"
    db.commit()

    report = generate_report(
        db,
        research_run_id=context["first_run"].id,
        analysis_id=context["first_analysis"].id,
    )

    assert report.status == "completed"
    assert report.research_run_id == context["first_run"].id
    assert report.analysis_id == context["first_analysis"].id
    assert report.version == 1
    sections = {section.section: section for section in report.sections}
    assert [item.ai_statement_id for item in sections["pricing"].items] == [context["first_statement"].id]


def test_generate_report_rejects_invalid_analysis_before_creating_report(db: Session):
    context = make_report_context(db)
    initial_count = db.query(ResearchReport).count()

    invalid_cases = (
        (context["first_run"].id, 999999, "AI analysis not found"),
        (context["second_run"].id, context["first_analysis"].id, "belong to the research run"),
        (context["first_run"].id, context["competitor_analysis"].id, "research-run-scoped"),
        (context["first_run"].id, context["pending_analysis"].id, "completed"),
        (context["first_run"].id, context["failed_analysis"].id, "completed"),
    )
    for research_run_id, analysis_id, message in invalid_cases:
        with pytest.raises((LookupError, ValueError), match=message):
            generate_report(
                db,
                research_run_id=research_run_id,
                analysis_id=analysis_id,
            )

    assert db.query(ResearchReport).count() == initial_count


def test_generate_report_creates_historical_version_for_each_explicit_run(db: Session):
    context = make_report_context(db)

    first = generate_report(
        db,
        research_run_id=context["first_run"].id,
        analysis_id=context["first_analysis"].id,
    )
    second = generate_report(
        db,
        research_run_id=context["first_run"].id,
        analysis_id=context["first_analysis"].id,
    )

    assert first.id != second.id
    assert first.version == 1
    assert second.version == 2
    assert first.status == "completed"
    assert second.status == "completed"


def test_generate_report_preserves_composition_failure_handling(db: Session, monkeypatch):
    context = make_report_context(db)
    analysis_id = context["first_analysis"].id
    original_compose = compose_report

    def fail_during_composition(session, report_id):
        original_add_all = session.add_all
        failed = False

        def fail_once(*args, **kwargs):
            nonlocal failed
            if not failed:
                failed = True
                raise RuntimeError("composition failed")
            return original_add_all(*args, **kwargs)

        monkeypatch.setattr(session, "add_all", fail_once)
        return original_compose(session, report_id)

    monkeypatch.setattr(research_reports_service, "compose_report", fail_during_composition)

    report = generate_report(
        db,
        research_run_id=context["first_run"].id,
        analysis_id=analysis_id,
    )

    reports = db.query(ResearchReport).all()
    assert len(reports) == 1
    assert report.status == "failed"
    assert reports[0].status == "failed"
    assert "composition failed" in reports[0].failure_reason

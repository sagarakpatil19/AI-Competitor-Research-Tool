from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.ai_comparison import AIComparison
from app.models.ai_statement import AIStatement
from app.models.research_report import ResearchReport, ResearchReportSection, ResearchReportSectionItem
from app.repositories import research_reports as report_repository
from app.schemas.research_report import (
    ResearchReportCreate,
    ResearchReportSectionCreate,
    ResearchReportSectionItemCreate,
)


REPORT_SECTIONS = (
    "company_overview",
    "products",
    "features",
    "pricing",
    "target_audience",
    "customer_feedback",
    "key_findings",
    "comparisons",
)
REPORT_SECTION_STATUSES = ("pending", "completed", "no_content", "failed")


def create_report(db: Session, data: ResearchReportCreate) -> ResearchReport:
    analysis = db.get(AIAnalysis, data.analysis_id)
    if analysis is None:
        raise LookupError("AI analysis not found")
    if analysis.research_run_id != data.research_run_id:
        raise ValueError("AI analysis must belong to the research run")
    if analysis.scope != "research_run":
        raise ValueError("Reports require a research-run-scoped AI analysis")
    if analysis.status != "completed":
        raise ValueError("Reports require a completed AI analysis")

    report = ResearchReport(
        research_run_id=data.research_run_id,
        analysis_id=data.analysis_id,
        status="pending",
        version=report_repository.next_version(db, data.research_run_id),
    )
    return report_repository.create_report(db, report)


def create_report_section(
    db: Session,
    data: ResearchReportSectionCreate,
) -> ResearchReportSection:
    report = report_repository.get_report(db, data.report_id)
    if report is None:
        raise LookupError("Research report not found")
    if data.section not in REPORT_SECTIONS:
        raise ValueError("Invalid report section")
    if data.status not in REPORT_SECTION_STATUSES:
        raise ValueError("Invalid report section status")

    section = ResearchReportSection(
        report_id=report.id,
        section=data.section,
        status=data.status,
        display_order=data.display_order,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return section


def create_report_section_item(
    db: Session,
    data: ResearchReportSectionItemCreate,
) -> ResearchReportSectionItem:
    section = db.get(ResearchReportSection, data.section_id)
    if section is None:
        raise LookupError("Research report section not found")
    report = section.report
    analysis = report.analysis

    statement = db.get(AIStatement, data.ai_statement_id) if data.ai_statement_id is not None else None
    comparison = db.get(AIComparison, data.ai_comparison_id) if data.ai_comparison_id is not None else None
    if data.item_type == "statement":
        if statement is None or comparison is not None:
            raise ValueError("Statement items require exactly one AI statement reference")
        if statement.analysis_id != analysis.id:
            raise ValueError("AI statement must belong to the report analysis")
    elif data.item_type == "comparison":
        if comparison is None or statement is not None:
            raise ValueError("Comparison items require exactly one AI comparison reference")
        if comparison.analysis_id != analysis.id:
            raise ValueError("AI comparison must belong to the report analysis")
    else:
        raise ValueError("Invalid report item type")

    item = ResearchReportSectionItem(
        section_id=section.id,
        item_type=data.item_type,
        ai_statement_id=data.ai_statement_id,
        ai_comparison_id=data.ai_comparison_id,
        display_order=data.display_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def complete_report(db: Session, report_id: int) -> ResearchReport:
    report = report_repository.get_report(db, report_id)
    if report is None:
        raise LookupError("Research report not found")
    report.status = "completed"
    report.completed_at = datetime.now(timezone.utc)
    return report_repository.save_report(db, report)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_comparison import AIComparison
from app.models.ai_statement import AIStatement
from app.models.research_report import ResearchReport, ResearchReportSection, ResearchReportSectionItem
from app.schemas.research_report_api import (
    ReportComparisonReferenceResponse,
    ReportStatementReferenceResponse,
    ResearchReportGenerateRequest,
    ResearchReportHistoryItemResponse,
    ResearchReportResponse,
    ResearchReportSectionItemResponse,
    ResearchReportSectionResponse,
)
from app.services import research_reports as report_service

router = APIRouter(prefix="/research-runs/{research_run_id}/reports", tags=["reports"])


def statement_to_response(statement: AIStatement) -> ReportStatementReferenceResponse:
    return ReportStatementReferenceResponse(
        id=statement.id,
        analysis_id=statement.analysis_id,
        statement_type=statement.statement_type,
        text=statement.text,
        support_status=statement.support_status,
        competitor_research_id=statement.competitor_research_id,
        section=statement.section,
        created_at=statement.created_at,
    )


def comparison_to_response(comparison: AIComparison) -> ReportComparisonReferenceResponse:
    return ReportComparisonReferenceResponse(
        id=comparison.id,
        analysis_id=comparison.analysis_id,
        comparison_type=comparison.comparison_type,
        dimension=comparison.dimension,
        statement=comparison.statement,
        support_status=comparison.support_status,
        competitor_research_ids=[item.competitor_research_id for item in comparison.competitors],
        created_at=comparison.created_at,
    )


def section_item_to_response(item: ResearchReportSectionItem) -> ResearchReportSectionItemResponse:
    return ResearchReportSectionItemResponse(
        id=item.id,
        item_type=item.item_type,
        display_order=item.display_order,
        ai_statement_id=item.ai_statement_id,
        ai_comparison_id=item.ai_comparison_id,
        statement=statement_to_response(item.statement) if item.statement is not None else None,
        comparison=comparison_to_response(item.comparison) if item.comparison is not None else None,
        created_at=item.created_at,
    )


def section_to_response(section: ResearchReportSection) -> ResearchReportSectionResponse:
    return ResearchReportSectionResponse(
        id=section.id,
        section=section.section,
        status=section.status,
        display_order=section.display_order,
        items=[section_item_to_response(item) for item in sorted(section.items, key=lambda item: (item.display_order, item.id))],
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


def report_to_response(report: ResearchReport) -> ResearchReportResponse:
    return ResearchReportResponse(
        id=report.id,
        research_run_id=report.research_run_id,
        analysis_id=report.analysis_id,
        status=report.status,
        version=report.version,
        completed_at=report.completed_at,
        failure_reason=report.failure_reason,
        created_at=report.created_at,
        updated_at=report.updated_at,
        sections=[section_to_response(section) for section in sorted(report.sections, key=lambda section: (section.display_order, section.id))],
    )


def report_history_to_response(report: ResearchReport) -> ResearchReportHistoryItemResponse:
    return ResearchReportHistoryItemResponse(
        id=report.id,
        research_run_id=report.research_run_id,
        analysis_id=report.analysis_id,
        status=report.status,
        version=report.version,
        completed_at=report.completed_at,
        failure_reason=report.failure_reason,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("", response_model=ResearchReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    research_run_id: int,
    payload: ResearchReportGenerateRequest,
    db: Session = Depends(get_db),
) -> ResearchReportResponse:
    try:
        report = report_service.generate_report(
            db,
            research_run_id=research_run_id,
            analysis_id=payload.analysis_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    report = report_service.get_report_for_research_run(db, research_run_id, report.id)
    return report_to_response(report)


@router.get("", response_model=list[ResearchReportHistoryItemResponse])
def list_reports(
    research_run_id: int,
    db: Session = Depends(get_db),
) -> list[ResearchReportHistoryItemResponse]:
    try:
        reports = report_service.list_reports_for_research_run(db, research_run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [report_history_to_response(report) for report in reports]


@router.get("/{report_id}", response_model=ResearchReportResponse)
def get_report(
    research_run_id: int,
    report_id: int,
    db: Session = Depends(get_db),
) -> ResearchReportResponse:
    try:
        report = report_service.get_report_for_research_run(db, research_run_id, report_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return report_to_response(report)

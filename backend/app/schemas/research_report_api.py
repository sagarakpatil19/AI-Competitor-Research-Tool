from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ReportStatus = Literal["pending", "running", "completed", "failed"]
ReportSectionStatus = Literal["pending", "completed", "no_content", "failed"]
ReportItemType = Literal["statement", "comparison"]


class ResearchReportGenerateRequest(BaseModel):
    analysis_id: int


class ReportStatementReferenceResponse(BaseModel):
    id: int
    analysis_id: int
    statement_type: str
    text: str
    support_status: str
    competitor_research_id: int | None
    section: str | None
    created_at: datetime


class ReportComparisonReferenceResponse(BaseModel):
    id: int
    analysis_id: int
    comparison_type: str
    dimension: str
    statement: str
    support_status: str
    competitor_research_ids: list[int]
    created_at: datetime


class ResearchReportSectionItemResponse(BaseModel):
    id: int
    item_type: ReportItemType
    display_order: int
    ai_statement_id: int | None
    ai_comparison_id: int | None
    statement: ReportStatementReferenceResponse | None
    comparison: ReportComparisonReferenceResponse | None
    created_at: datetime


class ResearchReportSectionResponse(BaseModel):
    id: int
    section: str
    status: ReportSectionStatus
    display_order: int
    items: list[ResearchReportSectionItemResponse]
    created_at: datetime
    updated_at: datetime


class ResearchReportResponse(BaseModel):
    id: int
    research_run_id: int
    analysis_id: int
    status: ReportStatus
    version: int
    completed_at: datetime | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    sections: list[ResearchReportSectionResponse]


class ResearchReportHistoryItemResponse(BaseModel):
    id: int
    research_run_id: int
    analysis_id: int
    status: ReportStatus
    version: int
    completed_at: datetime | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime

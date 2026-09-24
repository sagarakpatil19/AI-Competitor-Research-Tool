from typing import Literal

from pydantic import BaseModel, Field, model_validator


ReportStatus = Literal["pending", "running", "completed", "failed"]
ReportSectionStatus = Literal["pending", "completed", "no_content", "failed"]
ReportItemType = Literal["statement", "comparison"]


class ResearchReportCreate(BaseModel):
    research_run_id: int = Field(gt=0)
    analysis_id: int = Field(gt=0)


class ResearchReportSectionCreate(BaseModel):
    report_id: int = Field(gt=0)
    section: Literal[
        "company_overview",
        "products",
        "features",
        "pricing",
        "target_audience",
        "customer_feedback",
        "key_findings",
        "comparisons",
    ]
    status: ReportSectionStatus = "pending"
    display_order: int = Field(ge=0)


class ResearchReportSectionItemCreate(BaseModel):
    section_id: int = Field(gt=0)
    item_type: ReportItemType
    ai_statement_id: int | None = Field(default=None, gt=0)
    ai_comparison_id: int | None = Field(default=None, gt=0)
    display_order: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_reference(self) -> "ResearchReportSectionItemCreate":
        if self.item_type == "statement" and (self.ai_statement_id is None or self.ai_comparison_id is not None):
            raise ValueError("Statement items require exactly one AI statement reference")
        if self.item_type == "comparison" and (self.ai_comparison_id is None or self.ai_statement_id is not None):
            raise ValueError("Comparison items require exactly one AI comparison reference")
        return self

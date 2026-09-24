from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchReport(Base):
    __tablename__ = "research_reports"
    __table_args__ = (
        UniqueConstraint("research_run_id", "version", name="uq_research_reports_run_version"),
        Index("ix_research_reports_research_run_created", "research_run_id", "created_at"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_research_reports_status",
        ),
        CheckConstraint("version > 0", name="ck_research_reports_version_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_run_id: Mapped[int] = mapped_column(
        ForeignKey("research_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("ai_analyses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    research_run: Mapped["ResearchRun"] = relationship(back_populates="reports")
    analysis: Mapped["AIAnalysis"] = relationship(back_populates="reports")
    sections: Mapped[list["ResearchReportSection"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ResearchReportSection(Base):
    __tablename__ = "research_report_sections"
    __table_args__ = (
        UniqueConstraint("report_id", "section", name="uq_research_report_sections_report_section"),
        UniqueConstraint("report_id", "display_order", name="uq_research_report_sections_report_order"),
        Index("ix_research_report_sections_report_order", "report_id", "display_order"),
        CheckConstraint(
            "section IN ('company_overview', 'products', 'features', 'pricing', 'target_audience', 'customer_feedback', 'key_findings', 'comparisons')",
            name="ck_research_report_sections_section",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'no_content', 'failed')",
            name="ck_research_report_sections_status",
        ),
        CheckConstraint("display_order >= 0", name="ck_research_report_sections_display_order_nonnegative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        ForeignKey("research_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    report: Mapped[ResearchReport] = relationship(back_populates="sections")
    items: Mapped[list["ResearchReportSectionItem"]] = relationship(
        back_populates="section", cascade="all, delete-orphan"
    )


class ResearchReportSectionItem(Base):
    __tablename__ = "research_report_section_items"
    __table_args__ = (
        Index("ix_research_report_section_items_section_order", "section_id", "display_order"),
        UniqueConstraint("section_id", "display_order", name="uq_research_report_section_items_section_order"),
        CheckConstraint(
            "item_type IN ('statement', 'comparison')",
            name="ck_research_report_section_items_item_type",
        ),
        CheckConstraint("display_order >= 0", name="ck_research_report_section_items_display_order_nonnegative"),
        CheckConstraint(
            "(item_type = 'statement' AND ai_statement_id IS NOT NULL AND ai_comparison_id IS NULL) OR "
            "(item_type = 'comparison' AND ai_statement_id IS NULL AND ai_comparison_id IS NOT NULL)",
            name="ck_research_report_section_items_exact_reference",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("research_report_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    ai_statement_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_statements.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    ai_comparison_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_comparisons.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    section: Mapped[ResearchReportSection] = relationship(back_populates="items")
    statement: Mapped["AIStatement | None"] = relationship(back_populates="report_items")
    comparison: Mapped["AIComparison | None"] = relationship(back_populates="report_items")

from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorResearchSectionName(str, Enum):
    COMPANY_OVERVIEW = "company_overview"
    PRODUCTS = "products"
    FEATURES = "features"
    PRICING = "pricing"
    TARGET_AUDIENCE = "target_audience"
    CUSTOMER_FEEDBACK = "customer_feedback"


class CompetitorResearchSectionStatus(str, Enum):
    PENDING = "pending"
    COLLECTED = "collected"
    STRUCTURED = "structured"
    NO_EVIDENCE = "no_evidence"
    COLLECTION_FAILED = "collection_failed"
    NOT_APPLICABLE = "not_applicable"


class CompetitorResearchSection(Base):
    __tablename__ = "competitor_research_sections"
    __table_args__ = (
        UniqueConstraint("competitor_research_id", "section"),
        Index("ix_competitor_research_sections_research_status", "competitor_research_id", "status"),
        CheckConstraint(
            "section IN ('company_overview', 'products', 'features', 'pricing', 'target_audience', 'customer_feedback')",
            name="ck_competitor_research_sections_section",
        ),
        CheckConstraint(
            "status IN ('pending', 'collected', 'structured', 'no_evidence', 'collection_failed', 'not_applicable')",
            name="ck_competitor_research_sections_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_research_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="CASCADE"),
        nullable=False,
    )
    section: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CompetitorResearchSectionStatus.PENDING.value, server_default="pending"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    fact_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    competitor_research: Mapped["CompetitorResearch"] = relationship(back_populates="sections")

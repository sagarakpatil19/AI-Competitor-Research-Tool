from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorSource(Base):
    __tablename__ = "competitor_sources"
    __table_args__ = (UniqueConstraint("competitor_research_id", "canonical_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_research_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_research.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discovery_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="discovered", server_default="discovered")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    competitor_research: Mapped["CompetitorResearch"] = relationship(back_populates="sources")
    evidence: Mapped[list["CompetitorEvidence"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )
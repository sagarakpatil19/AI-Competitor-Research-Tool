from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitorResearch(Base):
    __tablename__ = "competitor_research"
    __table_args__ = (UniqueConstraint("competitor_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_id: Mapped[int] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    products_services: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_customers: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    competitor: Mapped["Competitor"] = relationship(back_populates="research")
    evidence: Mapped[list["CompetitorEvidence"]] = relationship(
        back_populates="competitor_research",
        cascade="all, delete-orphan",
    )
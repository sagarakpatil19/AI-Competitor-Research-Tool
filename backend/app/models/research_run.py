from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchRunStatus(str, Enum):
    SUBMITTED = "submitted"
    RESOLVING = "resolving"
    DISCOVERING = "discovering"
    VALIDATING = "validating"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchInputType(str, Enum):
    URL = "url"
    DOMAIN = "domain"
    COMPANY_NAME = "company_name"


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    input_value: Mapped[str] = mapped_column(String(2048), nullable=False)
    input_type: Mapped[ResearchInputType | None] = mapped_column(
        SqlEnum(
            ResearchInputType,
            name="research_input_type",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=True,
    )
    resolved_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ResearchRunStatus] = mapped_column(
        SqlEnum(
            ResearchRunStatus,
            name="research_run_status",
            native_enum=True,
            values_callable=lambda enum_type: [member.value for member in enum_type],
        ),
        nullable=False,
        default=ResearchRunStatus.SUBMITTED,
        server_default=ResearchRunStatus.SUBMITTED.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    competitors: Mapped[list["Competitor"]] = relationship(back_populates="research_run")
    discovery_runs: Mapped[list["CompetitorDiscoveryRun"]] = relationship(
        back_populates="research_run",
        cascade="all, delete-orphan",
    )
    discovery_candidates: Mapped[list["CompetitorDiscoveryCandidate"]] = relationship(
        back_populates="research_run",
        cascade="all, delete-orphan",
    )
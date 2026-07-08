from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Status

from .base import Base

if TYPE_CHECKING:
    from .job_task import JobTask
    from .sample import Sample


class Job(Base):
    __tablename__ = "jobs"

    sample_id: Mapped[int] = mapped_column(
        ForeignKey("samples.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    engine_version: Mapped[str] = mapped_column(
        nullable=False,
        default="1.0.0",
    )

    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status"),
        default=Status.PENDING,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sample: Mapped[Sample] = relationship(back_populates="jobs")
    tasks: Mapped[list[JobTask]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index(None, "sample_id", "engine_version", "status"),)

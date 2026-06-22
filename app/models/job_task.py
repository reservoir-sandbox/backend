from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Status, TaskType

from .base import Base

if TYPE_CHECKING:
    from .job import Job


class JobTask(Base):
    __tablename__ = "job_tasks"

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type"),
        nullable=False,
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

    error: Mapped[str | None] = mapped_column(nullable=True)

    job: Mapped[Job] = relationship(back_populates="tasks")

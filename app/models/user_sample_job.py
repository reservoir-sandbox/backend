from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserSampleJob(Base):
    __tablename__ = "user_sample_jobs"

    user_sample_id: Mapped[int] = mapped_column(
        ForeignKey("user_samples.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    pinned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("user_sample_id", "job_id"),)

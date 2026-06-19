from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.sample import Sample

from .base import Base

if TYPE_CHECKING:
    from .sample import Sample


class Job(Base):
    __tablename__ = "jobs"

    sample_id: Mapped[int] = mapped_column(
        ForeignKey("samples.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(default="pending", nullable=False)

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

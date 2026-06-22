from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .job import Job
    from .user_sample import UserSample


class Sample(Base):
    __tablename__ = "samples"

    size: Mapped[int] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)

    sha256: Mapped[str] = mapped_column(unique=True, nullable=False)
    object_name: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user_samples: Mapped[list[UserSample]] = relationship(
        back_populates="sample",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list[Job]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )

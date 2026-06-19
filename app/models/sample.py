from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .job import Job
    from .user import User


class Sample(Base):
    __tablename__ = "samples"

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[int] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)

    sha256: Mapped[str] = mapped_column(unique=True, nullable=False)
    object_name: Mapped[str] = mapped_column(nullable=False)

    status: Mapped[str] = mapped_column(default="uploaded", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped[User] = relationship(back_populates="samples")
    jobs: Mapped[list[Job]] = relationship(
        back_populates="sample", cascade="all, delete-orphan"
    )

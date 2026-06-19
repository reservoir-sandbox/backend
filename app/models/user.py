from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.auth.roles import Role

from .base import Base

if TYPE_CHECKING:
    from .sample import Sample


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role),
        default=Role.USER,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    samples: Mapped[list[Sample]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    __table_args__ = (Index(None, func.lower(username), unique=True),)

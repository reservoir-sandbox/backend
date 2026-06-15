from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserCRUD:
    async def create_user(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def get_by_id(self, session: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.scalar(stmt)
        return result

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.scalar(stmt)
        return result

    async def get_all_users(self, session: AsyncSession) -> Sequence[User]:
        stmt = select(User).order_by(User.id)
        result = await session.scalars(stmt)
        return result.all()

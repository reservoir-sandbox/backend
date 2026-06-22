from typing import Protocol, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


class UserCRUDProtocol(Protocol):
    async def create_user(self, session: AsyncSession, user: User) -> User: ...

    async def get_by_id(self, session: AsyncSession, user_id: int) -> User | None: ...

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> User | None: ...

    async def get_all_users(self, session: AsyncSession) -> Sequence[User]: ...

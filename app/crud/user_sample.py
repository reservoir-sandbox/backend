from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserSample


class UserSampleCRUD:
    async def create(
        self, session: AsyncSession, user_sample: UserSample
    ) -> UserSample:
        session.add(user_sample)
        await session.flush()
        return user_sample

    async def get_by_user_and_sample(
        self, session: AsyncSession, user_id: int, sample_id: int
    ) -> UserSample | None:
        stmt = select(UserSample).where(
            UserSample.user_id == user_id, UserSample.sample_id == sample_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

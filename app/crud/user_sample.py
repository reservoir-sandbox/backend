from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, UserSample


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

    async def get_samples_by_user(
        self, session: AsyncSession, user_id: int
    ) -> Sequence[RowMapping]:
        latest_job = (
            select(
                Job.sample_id,
                func.max(Job.id).label("latest_job_id"),
            )
            .group_by(Job.sample_id)
            .subquery()
        )

        stmt = (
            select(
                UserSample.sample_id,
                UserSample.filename,
                UserSample.uploaded_at,
                Job.id.label("latest_job_id"),
                Job.status.label("latest_job_status"),
            )
            .outerjoin(
                latest_job,
                latest_job.c.sample_id == UserSample.sample_id,
            )
            .outerjoin(
                Job,
                Job.id == latest_job.c.latest_job_id,
            )
            .where(UserSample.user_id == user_id)
            .order_by(UserSample.uploaded_at.desc())
        )

        result = await session.execute(stmt)
        return result.mappings().all()

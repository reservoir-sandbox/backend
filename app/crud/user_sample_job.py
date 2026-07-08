from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, UserSampleJob


class UserSampleJobCRUD:
    async def create(
        self, session: AsyncSession, user_sample_id: int, job_id: int
    ) -> None:
        stmt = (
            pg_insert(UserSampleJob)
            .values(user_sample_id=user_sample_id, job_id=job_id)
            .on_conflict_do_update(
                index_elements=["user_sample_id", "job_id"],
                set_={"pinned_at": func.now()},
            )
        )
        await session.execute(stmt)

    async def get(self, session: AsyncSession, user_sample_id: int) -> Sequence[Job]:
        stmt = (
            select(Job)
            .join(UserSampleJob, UserSampleJob.job_id == Job.id)
            .where(UserSampleJob.user_sample_id == user_sample_id)
            .order_by(UserSampleJob.pinned_at.desc())
        )
        result = await session.scalars(stmt)
        return result.all()

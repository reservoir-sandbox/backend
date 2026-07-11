from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import Status
from app.models import Job, UserSample, UserSampleJob


class JobCRUD:
    async def create(self, session: AsyncSession, job: Job) -> Job:
        session.add(job)
        await session.flush()
        return job

    async def get_by_id(
        self, session: AsyncSession, job_id: int, for_update: bool = False
    ) -> Job | None:
        stmt = select(Job).where(Job.id == job_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await session.scalar(stmt)
        return result

    async def get_latest_by_sample_id(
        self, session: AsyncSession, sample_id: int
    ) -> Job | None:
        stmt = (
            select(Job)
            .where(Job.sample_id == sample_id)
            .order_by(Job.created_at.desc())
        )
        result = await session.scalar(stmt)
        return result

    async def get_active_by_sample_and_version(
        self, session: AsyncSession, sample_id: int, engine_version: str
    ) -> Job | None:
        stmt = (
            select(Job)
            .where(
                Job.sample_id == sample_id,
                Job.engine_version == engine_version,
                Job.status.in_([Status.PENDING, Status.RUNNING, Status.COMPLETED]),
            )
            .order_by(Job.created_at.desc())
        )
        result = await session.scalars(stmt)
        return result.first()

    async def get_job_details_by_id(
        self, session: AsyncSession, job_id: int, user_id: int
    ) -> Job | None:
        stmt = (
            select(Job)
            .join(UserSampleJob, UserSampleJob.job_id == Job.id)
            .join(UserSample, UserSample.id == UserSampleJob.user_sample_id)
            .where(Job.id == job_id, UserSample.user_id == user_id)
            .options(
                selectinload(Job.tasks),
            )
        )
        result = await session.scalar(stmt)
        return result

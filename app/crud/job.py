from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job


class JobCRUD:
    async def create(self, session: AsyncSession, job: Job) -> Job:
        session.add(job)
        await session.flush()
        return job

    async def get_by_id(self, session: AsyncSession, job_id: int) -> Job | None:
        stmt = select(Job).where(Job.id == job_id)
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

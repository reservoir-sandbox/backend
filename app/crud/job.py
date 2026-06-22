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

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import JobTask


class JobTaskCRUD:
    async def create(self, session: AsyncSession, job_task: JobTask) -> JobTask:
        session.add(job_task)
        await session.flush()
        return job_task

    async def get_by_task_id(
        self, session: AsyncSession, task_id: int
    ) -> JobTask | None:
        stmt = select(JobTask).where(JobTask.id == task_id)
        result = await session.scalar(stmt)
        return result

    async def get_tasks_by_job_id(
        self, session: AsyncSession, job_id: int
    ) -> Sequence[JobTask]:
        stmt = select(JobTask).where(JobTask.job_id == job_id)
        result = await session.scalars(stmt)
        return result.all()

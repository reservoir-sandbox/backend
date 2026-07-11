from typing import Protocol, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, JobTask


class JobCRUDProtocol(Protocol):
    async def create(self, session: AsyncSession, job: Job) -> Job: ...

    async def get_by_id(
        self, session: AsyncSession, job_id: int, for_update: bool = False
    ) -> Job | None: ...

    async def get_latest_by_sample_id(
        self, session: AsyncSession, sample_id: int
    ) -> Job | None: ...

    async def get_active_by_sample_and_version(
        self, session: AsyncSession, sample_id: int, engine_version: str
    ) -> Job | None: ...

    async def get_job_details_by_id(
        self, session: AsyncSession, job_id: int, user_id: int
    ) -> Job | None: ...


class JobTaskCRUDProtocol(Protocol):
    async def create(self, session: AsyncSession, job_task: JobTask) -> JobTask: ...

    async def get_by_task_id(
        self, session: AsyncSession, task_id: int
    ) -> JobTask | None: ...

    async def get_tasks_by_job_id(
        self, session: AsyncSession, job_id: int
    ) -> Sequence[JobTask]: ...

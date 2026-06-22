from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TaskType
from app.models import Job, JobTask, Sample
from app.protocols import JobCRUDProtocol, JobTaskCRUDProtocol


class JobService:
    def __init__(
        self,
        job_crud: JobCRUDProtocol,
        job_task_crud: JobTaskCRUDProtocol,
    ):
        self.job_crud = job_crud
        self.job_task_crud = job_task_crud

    async def create_job_for_sample(
        self, session: AsyncSession, sample: Sample, user_id: int
    ) -> Job:
        job = await self.job_crud.create(session, Job(sample_id=sample.id))

        for task_type in TaskType:
            await self.job_task_crud.create(
                session,
                JobTask(
                    job_id=job.id,
                    task_type=task_type,
                ),
            )

        return job

    async def get_latest_job_by_sample_id(
        self, session: AsyncSession, sample_id: int
    ) -> Job | None:
        return await self.job_crud.get_latest_by_sample_id(session, sample_id)

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import TaskType
from app.enums.status import Status
from app.exceptions import JobNotFoundError, TaskNotFoundError
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
        self, session: AsyncSession, sample: Sample, engine_version: str
    ) -> Job:
        job = await self.job_crud.create(
            session, Job(sample_id=sample.id, engine_version=engine_version)
        )

        for task_type in TaskType:
            await self.job_task_crud.create(
                session,
                JobTask(
                    job_id=job.id,
                    task_type=task_type,
                ),
            )
        return job

    async def get_active_job(
        self, session: AsyncSession, sample_id: int, engine_version: str
    ) -> Job | None:
        return await self.job_crud.get_active_by_sample_and_version(
            session, sample_id, engine_version
        )

    async def get_latest_job_by_sample_id(
        self, session: AsyncSession, sample_id: int
    ) -> Job | None:
        return await self.job_crud.get_latest_by_sample_id(session, sample_id)

    async def get_job_details_by_id(
        self, session: AsyncSession, job_id: int, user_id: int
    ) -> Job | None:
        job = await self.job_crud.get_job_details_by_id(session, job_id, user_id)
        if job is None:
            raise JobNotFoundError()
        return job

    async def get_job_tasks_by_job_id(
        self, session: AsyncSession, job_id: int
    ) -> list[JobTask]:
        result = await self.job_task_crud.get_tasks_by_job_id(session, job_id)
        return list(result)

    async def _recompute_job_status(
        self, session: AsyncSession, job_id: int, now: datetime
    ) -> None:
        job = await self.job_crud.get_by_id(session, job_id, for_update=True)
        if not job:
            return

        tasks = await self.job_task_crud.get_tasks_by_job_id(session, job_id)
        if not tasks:
            return

        statuses = {task.status for task in tasks}
        terminal = {Status.COMPLETED, Status.FAILED}

        starts = [task.started_at for task in tasks if task.started_at]
        finishes = [task.finished_at for task in tasks if task.finished_at]

        if starts and job.started_at is None:
            job.started_at = min(starts)

        if statuses.issubset(terminal):
            job.status = (
                Status.FAILED if Status.FAILED in statuses else Status.COMPLETED
            )
            job.started_at = min(starts) if starts else now
            job.finished_at = max(finishes) if finishes else now
        else:
            job.status = Status.RUNNING

    async def apply_task_result(
        self,
        session: AsyncSession,
        task_id: int,
        status: Status,
        report_object_name: str | None,
        result: dict | None,
        error: str | None,
        started_at: datetime | None,
        finished_at: datetime | None,
    ) -> JobTask:
        task = await self.job_task_crud.get_by_task_id(session, task_id)
        if task is None:
            raise TaskNotFoundError()

        now = datetime.now(timezone.utc)
        task.status = status
        task.started_at = started_at or task.started_at or now
        task.finished_at = finished_at or now
        task.report_object_name = report_object_name
        task.result = result
        task.error = error

        await self._recompute_job_status(session, task.job_id, now)
        return task

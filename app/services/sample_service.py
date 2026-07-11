from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core import Settings, logger
from app.exceptions import FileTooLargeError, InvalidELFError, SampleNotFoundError
from app.models import Job, Sample, UserSample
from app.protocols import (
    SampleCRUDProtocol,
    UserSampleCRUDProtocol,
    UserSampleJobCRUDProtocol,
)
from app.schemas.sample import SampleListItem
from app.utils import calculate_sha256

from .job_launcher_service import JobLauncher
from .job_service import JobService
from .storage_service import StorageService


class SampleService:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ELF_MAGIC = b"\x7fELF"

    def __init__(
        self,
        storage_service: StorageService,
        job_service: JobService,
        job_launcher: JobLauncher,
        sample_crud: SampleCRUDProtocol,
        user_sample_crud: UserSampleCRUDProtocol,
        user_sample_job_crud: UserSampleJobCRUDProtocol,
        settings: Settings,
    ):
        self.storage_service = storage_service
        self.job_service = job_service
        self.job_launcher = job_launcher
        self.sample_crud = sample_crud
        self.user_sample_crud = user_sample_crud
        self.user_sample_job_crud = user_sample_job_crud
        self.settings = settings

    def _validate_elf(self, file_stream: BinaryIO) -> int:
        # Проверяет размер файла
        size = file_stream.seek(0, 2)
        if size > self.MAX_FILE_SIZE:
            raise FileTooLargeError()
        file_stream.seek(0)

        # Проверяет магические байты ELF
        magic_bytes = file_stream.read(4)
        if magic_bytes != self.ELF_MAGIC:
            raise InvalidELFError()
        file_stream.seek(0)
        return size

    async def _pin_job(
        self, session: AsyncSession, user_sample: UserSample, job: Job
    ) -> None:
        await self.user_sample_crud.set_current_job(session, user_sample, job)
        await self.user_sample_job_crud.create(session, user_sample.id, job.id)

    async def _launch(self, session: AsyncSession, job: Job, sample: Sample) -> None:
        tasks = await self.job_service.get_job_tasks_by_job_id(session, job.id)
        await session.commit()
        try:
            await run_in_threadpool(self.job_launcher.launch_job, job, sample, tasks)
        except Exception as e:
            logger.error(f"Failed to launch job {job.id}: {e}")

    async def upload_sample(
        self, sample: UploadFile, user_id: int, session: AsyncSession
    ) -> Job:
        file_stream: BinaryIO = sample.file
        size = self._validate_elf(file_stream)
        sha256_hash = calculate_sha256(file_stream)
        engine_version = self.settings.engine_version

        existing_sample = await self.sample_crud.get_by_sha256(session, sha256_hash)
        if existing_sample:
            user_sample = await self.user_sample_crud.get_by_user_and_sample(
                session, user_id, existing_sample.id
            )
            if not user_sample:
                user_sample = await self.user_sample_crud.create(
                    session,
                    UserSample(
                        user_id=user_id,
                        sample_id=existing_sample.id,
                        filename=sample.filename,
                    ),
                )

            job = await self.job_service.get_active_job(
                session, existing_sample.id, engine_version
            )
            launch = job is None
            if job is None:
                job = await self.job_service.create_job_for_sample(
                    session, existing_sample, engine_version
                )
            await self._pin_job(session, user_sample, job)
            if launch:
                await self._launch(session, job, existing_sample)
            return job

        await self.storage_service.upload_file(file_stream, sha256_hash)

        sample_model = await self.sample_crud.create(
            session,
            Sample(
                size=size,
                sha256=sha256_hash,
                object_name=f"uploads/{sha256_hash}",
            ),
        )

        user_sample = await self.user_sample_crud.create(
            session,
            UserSample(
                user_id=user_id,
                sample_id=sample_model.id,
                filename=sample.filename,
            ),
        )
        job = await self.job_service.create_job_for_sample(
            session, sample_model, engine_version
        )
        await self._pin_job(session, user_sample, job)
        await self._launch(session, job, sample_model)
        return job

    async def get_history_jobs(
        self, sample_id: int, user_id: int, session: AsyncSession
    ) -> list[Job]:
        user_sample = await self.user_sample_crud.get_by_user_and_sample(
            session, user_id, sample_id
        )
        if not user_sample:
            raise SampleNotFoundError()
        result = await self.user_sample_job_crud.get(session, user_sample.id)
        return list(result)

    async def get_samples(
        self, user_id: int, session: AsyncSession
    ) -> list[SampleListItem]:
        result = await self.user_sample_crud.get_samples_by_user(session, user_id)
        curr_engine_version = self.settings.engine_version
        return [
            SampleListItem(
                **row,
                analysis_stale=(
                    row["engine_version"] is not None
                    and tuple(map(int, row["engine_version"].split(".")))
                    < tuple(map(int, curr_engine_version.split(".")))
                ),
            )
            for row in result
        ]

    async def delete_user_sample(
        self, sample_id: int, user_id: int, session: AsyncSession
    ) -> None:
        user_sample = await self.user_sample_crud.get_by_user_and_sample(
            session, user_id, sample_id
        )
        if not user_sample:
            return
        await session.delete(user_sample)

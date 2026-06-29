from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import Settings
from app.enums import Status
from app.exceptions import FileTooLargeError, InvalidELFError
from app.models import Job, Sample, UserSample
from app.protocols import SampleCRUDProtocol, UserSampleCRUDProtocol
from app.schemas.sample import SampleListItem
from app.utils import calculate_sha256

from .job_service import JobService
from .storage_service import StorageService


class SampleService:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ELF_MAGIC = b"\x7fELF"

    def __init__(
        self,
        storage_service: StorageService,
        job_service: JobService,
        sample_crud: SampleCRUDProtocol,
        user_sample_crud: UserSampleCRUDProtocol,
        settings: Settings,
    ):
        self.storage_service = storage_service
        self.job_service = job_service
        self.sample_crud = sample_crud
        self.user_sample_crud = user_sample_crud
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

    async def upload_sample(
        self, sample: UploadFile, user_id: int, session: AsyncSession
    ) -> Job:
        file_stream: BinaryIO = sample.file
        size = self._validate_elf(file_stream)
        sha256_hash = calculate_sha256(file_stream)

        existing_sample = await self.sample_crud.get_by_sha256(session, sha256_hash)
        if existing_sample:
            user_sample = await self.user_sample_crud.get_by_user_and_sample(
                session, user_id, existing_sample.id
            )
            if not user_sample:
                await self.user_sample_crud.create(
                    session,
                    UserSample(
                        user_id=user_id,
                        sample_id=existing_sample.id,
                        filename=sample.filename,
                    ),
                )

            job = await self.job_service.get_latest_job_by_sample_id(
                session, existing_sample.id
            )
            if (job is None) or (
                job.status not in (Status.PENDING, Status.RUNNING, Status.COMPLETED)
            ):
                job = await self.job_service.create_job_for_sample(
                    session, existing_sample, user_id
                )

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

        await self.user_sample_crud.create(
            session,
            UserSample(
                user_id=user_id,
                sample_id=sample_model.id,
                filename=sample.filename,
            ),
        )
        return await self.job_service.create_job_for_sample(
            session, sample_model, user_id
        )

    async def get_samples(
        self, user_id: int, session: AsyncSession
    ) -> list[SampleListItem]:
        result = await self.user_sample_crud.get_samples_by_user(session, user_id)
        return [SampleListItem(**row) for row in result]

    async def delete_user_sample(
        self, sample_id: int, user_id: int, session: AsyncSession
    ) -> None:
        user_sample = await self.user_sample_crud.get_by_user_and_sample(
            session, user_id, sample_id
        )
        if not user_sample:
            return
        await session.delete(user_sample)

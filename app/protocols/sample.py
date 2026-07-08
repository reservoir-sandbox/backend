from typing import Protocol, Sequence

from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, Sample, UserSample


class SampleCRUDProtocol(Protocol):
    async def create(self, session: AsyncSession, sample: Sample) -> Sample: ...

    async def get_by_sha256(
        self, session: AsyncSession, sha256: str
    ) -> Sample | None: ...

    async def get_by_id(
        self, session: AsyncSession, sample_id: int
    ) -> Sample | None: ...


class UserSampleCRUDProtocol(Protocol):
    async def create(
        self, session: AsyncSession, user_sample: UserSample
    ) -> UserSample: ...

    async def set_current_job(
        self, session: AsyncSession, user_sample: UserSample, job: Job
    ) -> None: ...

    async def get_by_user_and_sample(
        self, session: AsyncSession, user_id: int, sample_id: int
    ) -> UserSample | None: ...

    async def get_samples_by_user(
        self, session: AsyncSession, user_id: int
    ) -> Sequence[RowMapping]: ...


class UserSampleJobCRUDProtocol(Protocol):
    async def create(
        self, session: AsyncSession, user_sample_id: int, job_id: int
    ) -> None: ...

    async def get(
        self, session: AsyncSession, user_sample_id: int
    ) -> Sequence[Job]: ...

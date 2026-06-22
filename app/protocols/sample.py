from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Sample, UserSample


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

    async def get_by_user_and_sample(
        self, session: AsyncSession, user_id: int, sample_id: int
    ) -> UserSample | None: ...

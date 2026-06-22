from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Sample


class SampleCRUD:
    async def create(self, session: AsyncSession, sample: Sample) -> Sample:
        session.add(sample)
        await session.flush()
        return sample

    async def get_by_sha256(self, session: AsyncSession, sha256: str) -> Sample | None:
        stmt = select(Sample).where(Sample.sha256 == sha256)
        result = await session.scalar(stmt)
        return result

    async def get_by_id(self, session: AsyncSession, sample_id: int) -> Sample | None:
        stmt = select(Sample).where(Sample.id == sample_id)
        result = await session.scalar(stmt)
        return result

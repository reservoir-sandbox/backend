from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import RequireRole
from app.auth.schemas import CurrentUser
from app.dependencies import get_db_session, get_sample_service
from app.enums import Role
from app.schemas import JobRead, SampleListItem
from app.services import SampleService

router = APIRouter()


@router.post("/samples", response_model=JobRead, status_code=201)
# @limiter.limit("1/minute")
async def upload_sample(
    sample: UploadFile,
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: SampleService = Depends(get_sample_service),
):
    return await service.upload_sample(sample, current_user.id, session)


@router.get("/samples", response_model=list[SampleListItem], status_code=200)
async def get_samples(
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: SampleService = Depends(get_sample_service),
):
    return await service.get_samples(current_user.id, session)


@router.delete("/samples/{id:int}", status_code=204)
async def delete_user_sample(
    id: int,
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: SampleService = Depends(get_sample_service),
):
    await service.delete_user_sample(id, current_user.id, session)


@router.get("/samples/{id:int}/jobs", response_model=list[JobRead], status_code=200)
async def get_history_jobs(
    id: int,
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: SampleService = Depends(get_sample_service),
):
    return await service.get_history_jobs(id, current_user.id, session)

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_sample_service
from app.auth.permissions import RequireRole
from app.auth.schemas import CurrentUser
from app.db import db_helper
from app.enums import Role
from app.schemas import JobRead
from app.services import SampleService

router = APIRouter()


@router.post("/samples", response_model=JobRead, status_code=201)
# @limiter.limit("1/minute")
async def upload_sample(
    sample: UploadFile,
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: SampleService = Depends(get_sample_service),
):
    return await service.upload_sample(sample, current_user.id, session)

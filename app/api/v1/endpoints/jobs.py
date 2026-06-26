from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import RequireRole
from app.auth.schemas import CurrentUser
from app.dependencies import get_db_session, get_job_service
from app.enums import Role
from app.schemas import JobDetails
from app.services import JobService

router = APIRouter()


@router.get("/jobs/{id:int}", response_model=JobDetails, status_code=200)
# @limiter.limit("1/minute")
async def get_job_details(
    id: int,
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: JobService = Depends(get_job_service),
):
    result = await service.get_job_details_by_id(
        session, job_id=id, user_id=current_user.id
    )
    return JobDetails.model_validate(result)

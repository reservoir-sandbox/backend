from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import RequireRole
from app.auth.schemas import CurrentUser
from app.dependencies import get_db_session, get_user_service
from app.enums import Role
from app.schemas import UserRead
from app.services import UserService

router = APIRouter()


@router.get("/about_me", response_model=UserRead)
async def about(
    current_user: CurrentUser = Depends(RequireRole(Role.USER)),
    session: AsyncSession = Depends(get_db_session),
    service: UserService = Depends(get_user_service),
):
    user = await service.get_by_id(
        session=session,
        user_id=current_user.id,
    )
    return UserRead.model_validate(user)

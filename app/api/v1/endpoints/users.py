from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_user_service
from app.db import db_helper
from app.schemas import UserRead
from app.services import UserService

router = APIRouter()


@router.get("/about_me", response_model=UserRead)
async def about(
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: UserService = Depends(get_user_service),
):
    user = await service.get_by_id(session=session, user_id=current_user_id)
    return UserRead.model_validate(user)

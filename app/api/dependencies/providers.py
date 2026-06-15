from fastapi import Depends

from app.core import Settings, get_settings
from app.crud import UserCRUD
from app.services import AuthService, UserService

from .repositories import get_user_crud


async def get_user_service(user_crud: UserCRUD = Depends(get_user_crud)):
    return UserService(user_crud)


async def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    settings: Settings = Depends(get_settings),
):
    return AuthService(user_service, settings)

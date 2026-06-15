from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core import API_V1_PREFIX
from app.services import AuthService

from .providers import get_auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/login")


def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> int:
    return service.get_user_id_from_token(token)

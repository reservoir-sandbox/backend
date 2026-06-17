from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies import get_auth_service
from app.auth.schemas import CurrentUser
from app.core import API_V1_PREFIX
from app.services import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_V1_PREFIX}/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> CurrentUser:
    return service.get_user_from_access_token(token)

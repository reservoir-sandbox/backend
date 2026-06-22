from contextlib import suppress

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_auth_service,
    get_db_session,
    get_redis_client,
    get_user_service,
)
from app.exceptions import TokenExpiredError, TokenInvalidError
from app.schemas import Token, UserRead, UserRegister
from app.services import AuthService, UserService
from app.utils import set_refresh_cookie

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
# @limiter.limit("1/minute")
async def register(
    request: Request,
    user: UserRegister,
    session: AsyncSession = Depends(get_db_session),
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(session, user)


@router.post("/login", response_model=Token)
# @limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    service: AuthService = Depends(get_auth_service),
):
    access_token, refresh_token = await service.auth_user(
        session, redis_client, form_data.username.lower(), form_data.password
    )

    set_refresh_cookie(response, refresh_token, service)

    return Token(access_token=access_token)


@router.post("/refresh", response_model=Token)
# @limiter.limit("3/minute")
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("refresh_token", "")

    access_token, new_refresh_token = await service.refresh_token(
        session, redis_client, refresh_token
    )

    set_refresh_cookie(response, new_refresh_token, service)

    return Token(access_token=access_token)


@router.post("/logout")
# @limiter.limit("3/minute")
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis_client),
    service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("refresh_token", "")

    if refresh_token:
        with suppress(TokenInvalidError, TokenExpiredError):
            await service.remove_refresh_token(session, redis_client, refresh_token)

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=service.settings.cookie_secure,
        samesite=service.settings.cookie_samesite,
        path="/",
    )

    return {"message": "logout successfully!"}

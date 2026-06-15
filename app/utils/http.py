from fastapi import Response

from app.services import AuthService


def set_refresh_cookie(
    response: Response, refresh_token: str, service: AuthService
) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=service.settings.cookie_secure,
        samesite=service.settings.cookie_samesite,
        path="/",
        max_age=60 * service.settings.refresh_token_expire_m,
    )

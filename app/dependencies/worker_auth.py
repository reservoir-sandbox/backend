from hmac import compare_digest

from fastapi import Depends, Header

from app.core import Settings, get_settings
from app.exceptions import AccessDenied


def verify_worker_token(
    x_worker_token: str = Header(...),
    settings: Settings = Depends(get_settings),
) -> None:
    if not compare_digest(x_worker_token, settings.worker_callback_secret):
        raise AccessDenied()

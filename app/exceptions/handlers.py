from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .custom import AppException


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI application.
    """
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_any_exception(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

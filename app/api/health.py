import asyncio

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core import logger
from app.db import db_helper, redis_helper

router = APIRouter()


@router.get("/health/live")
async def liveness_probe():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_probe():
    try:
        postgres_status = await asyncio.wait_for(db_helper.ping(), timeout=3)
    except Exception as e:
        logger.warning(f"Postgres health check failed: {e}")
        postgres_status = False

    try:
        redis_status = await asyncio.wait_for(redis_helper.ping(), timeout=3)
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_status = False

    overall_ok = postgres_status and redis_status

    payload = {
        "status": "ok" if overall_ok else "error",
        "services": {
            "postgres": "ok" if postgres_status else "error",
            "redis": "ok" if redis_status else "error",
        },
    }

    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content=payload,
    )

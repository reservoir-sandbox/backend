import asyncio

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.db import DatabaseClient, RedisClient

router = APIRouter()


@router.get("/health/live")
async def liveness_probe():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_probe(request: Request):
    db: DatabaseClient = request.app.state.db
    redis: RedisClient = request.app.state.redis

    postgres_result, redis_result = await asyncio.gather(
        asyncio.wait_for(db.ping(), timeout=3),
        asyncio.wait_for(redis.ping(), timeout=3),
        return_exceptions=True,
    )

    postgres_status = (
        False if isinstance(postgres_result, Exception) else postgres_result
    )
    redis_status = False if isinstance(redis_result, Exception) else redis_result

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

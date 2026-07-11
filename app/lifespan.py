from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import get_settings
from app.db import DatabaseClient, RedisClient, S3Client
from app.services import build_job_launcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    app.state.db = DatabaseClient(
        url=settings.database_url,
    )

    app.state.redis = RedisClient(
        url=settings.redis_url,
    )

    app.state.s3 = S3Client(
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        endpoint_url=settings.s3_endpoint_url,
        bucket_name=settings.s3_bucket_name,
    )

    app.state.job_launcher = build_job_launcher(settings)

    yield

    await app.state.db.dispose()
    await app.state.redis.close()

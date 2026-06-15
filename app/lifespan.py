from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import db_helper, redis_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    yield
    # shutdown code
    await db_helper.dispose()
    await redis_helper.close()

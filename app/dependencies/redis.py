from typing import cast

import redis.asyncio as redis
from fastapi import Request


def get_redis_client(request: Request) -> redis.Redis:
    return cast(redis.Redis, request.app.state.redis.get_client())

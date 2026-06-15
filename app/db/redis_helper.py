import redis.asyncio as redis

from app.core import get_settings


class RedisHelper:
    def __init__(self, url: str):
        self.client = redis.from_url(url)

    def get_client(self) -> redis.Redis:
        return self.client

    async def close(self) -> None:
        await self.client.aclose()

    async def ping(self) -> bool:
        try:
            return bool(await self.client.execute_command("PING"))
        except Exception:
            return False


settings = get_settings()
redis_helper = RedisHelper(url=settings.redis_url)

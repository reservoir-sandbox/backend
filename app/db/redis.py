import redis.asyncio as redis


class RedisClient:
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

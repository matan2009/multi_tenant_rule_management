import os
import redis.asyncio as redis


redis_client = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


async def increment_request_count(key: str) -> int:
    return await redis_client.incr(key)


async def set_expire_time(key: str, time_frame: int):
    await redis_client.expire(key, time_frame)

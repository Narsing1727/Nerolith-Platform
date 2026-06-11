from fastapi import Request, HTTPException
import redis.asyncio as aioredis
from config.settings import settings

RATE_LIMITS = {
    "default": {"requests": 100, "window": 60},
    "analyze": {"requests": 20, "window": 60},
}


async def check_rate_limit(request: Request):
    client = aioredis.from_url(settings.redis_url)
    auth = request.headers.get("Authorization", "anonymous")
    endpoint = "analyze" if "analyze" in request.url.path else "default"
    limit = RATE_LIMITS[endpoint]
    key = f"ratelimit:{endpoint}:{auth}"

    count = await client.incr(key)
    if count == 1:
        await client.expire(key, limit["window"])

    await client.aclose()

    if count > limit["requests"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit['requests']} requests per {limit['window']}s."
        )
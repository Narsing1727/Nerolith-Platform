from datetime import datetime
import redis
import asyncpg
from config.settings import settings


async def get_system_metrics() -> dict:
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        queue_lengths = {
            "priority_high": r.llen("priority_high"),
            "priority_normal": r.llen("priority_normal"),
            "priority_low": r.llen("priority_low"),
            "callbacks": r.llen("callbacks")
        }
        r.close()
        metrics["services"]["redis"] = "healthy"
        metrics["queues"] = queue_lengths
    except Exception as e:
        metrics["services"]["redis"] = f"unhealthy: {str(e)}"

    try:
        conn = await asyncpg.connect(settings.database_url.replace("+asyncpg", ""))
        await conn.fetchval("SELECT 1")
        await conn.close()
        metrics["services"]["postgres"] = "healthy"
    except Exception as e:
        metrics["services"]["postgres"] = f"unhealthy: {str(e)}"

    return metrics
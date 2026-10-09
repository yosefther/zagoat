from functools import lru_cache

from redis import Redis

from app.config import Settings


@lru_cache
def get_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis_url,
        socket_timeout=settings.healthcheck_timeout_seconds,
        socket_connect_timeout=settings.healthcheck_timeout_seconds,
    )

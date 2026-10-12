from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from redis import Redis

from app.config import Settings, get_settings


@lru_cache
def get_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis_url,
        socket_timeout=settings.healthcheck_timeout_seconds,
        socket_connect_timeout=settings.healthcheck_timeout_seconds,
    )


def redis_dependency(settings: Annotated[Settings, Depends(get_settings)]) -> Redis:
    return get_redis(settings)


RedisClient = Annotated[Redis, Depends(redis_dependency)]

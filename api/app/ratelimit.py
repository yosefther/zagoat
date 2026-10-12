"""Fixed-window rate limits stored in Redis."""

from dataclasses import dataclass

from fastapi import Request, status
from redis import Redis

from app.clock import utcnow
from app.errors import AppError


@dataclass(frozen=True)
class Window:
    count: int
    limit: int
    retry_after_seconds: int

    @property
    def allowed(self) -> bool:
        return self.count <= self.limit


def hit(redis: Redis, name: str, subject: str, limit: int, window_seconds: int) -> Window:
    """Count one attempt and report whether it is within the limit."""
    now = int(utcnow().timestamp())
    window_start = now - now % window_seconds
    key = f"rl:{name}:{subject}:{window_start}"
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    count = int(pipe.execute()[0])
    return Window(count=count, limit=limit, retry_after_seconds=window_start + window_seconds - now)


def peek(redis: Redis, name: str, subject: str, window_seconds: int) -> int:
    """Return the current count without adding an attempt."""
    now = int(utcnow().timestamp())
    window_start = now - now % window_seconds
    value = redis.get(f"rl:{name}:{subject}:{window_start}")
    return int(value) if value is not None else 0


def enforce(window: Window, message: str) -> None:
    if not window.allowed:
        raise AppError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            message,
            headers={"Retry-After": str(window.retry_after_seconds)},
            extra={"retry_after_seconds": window.retry_after_seconds},
        )


def client_ip(request: Request) -> str:
    # In production uvicorn runs with --proxy-headers behind the reverse proxy, so this is
    # the real client address.
    return request.client.host if request.client else "unknown"

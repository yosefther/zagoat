from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, get_settings
from app.db import get_engine
from app.redis_client import get_redis

router = APIRouter()

CheckState = Literal["ok", "down"]


class HealthResponse(BaseModel):
    status: CheckState
    checks: dict[str, CheckState]


def _check_database(settings: Settings) -> CheckState:
    try:
        with get_engine(settings).connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return "down"
    return "ok"


def _check_redis(settings: Settings) -> CheckState:
    try:
        get_redis(settings).ping()
    except RedisError:
        return "down"
    return "ok"


@router.get("/healthz", response_model=HealthResponse)
def healthz(
    response: Response, settings: Annotated[Settings, Depends(get_settings)]
) -> HealthResponse:
    checks = {"database": _check_database(settings), "redis": _check_redis(settings)}
    healthy = all(state == "ok" for state in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(status="ok" if healthy else "down", checks=checks)

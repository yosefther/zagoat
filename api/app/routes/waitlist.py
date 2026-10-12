from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.dialects.postgresql import insert

from app.config import Settings, get_settings
from app.db import DbSession
from app.models import WaitlistEntry
from app.ratelimit import client_ip, enforce, hit
from app.redis_client import RedisClient
from app.security.csrf import require_csrf

router = APIRouter()


class WaitlistRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    consent: bool
    source: str | None = Field(default=None, max_length=64)

    @field_validator("consent")
    @classmethod
    def _consent_given(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Tick the box to agree to launch emails.")
        return value


class WaitlistResponse(BaseModel):
    status: Literal["joined"]


@router.post("/waitlist", response_model=WaitlistResponse, dependencies=[Depends(require_csrf)])
def join_waitlist(
    body: WaitlistRequest,
    request: Request,
    db: DbSession,
    redis: RedisClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WaitlistResponse:
    enforce(
        hit(redis, "waitlist", client_ip(request), settings.ip_attempts_per_hour, 3600),
        "Too many signup attempts from your network. Try again in an hour.",
    )
    # Joining twice is not an error, and the response never reveals who is already listed.
    db.execute(
        insert(WaitlistEntry)
        .values(email=body.email.lower(), source=body.source, consent=True)
        .on_conflict_do_nothing(index_elements=[WaitlistEntry.email])
    )
    db.commit()
    return WaitlistResponse(status="joined")

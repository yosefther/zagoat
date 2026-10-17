import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import DbSession
from app.errors import AppError
from app.models import Subscription, User
from app.plans import plan_for
from app.redis_client import RedisClient
from app.routes.problems import UsageOut
from app.security.csrf import ANONYMOUS, issue_token, require_csrf, set_csrf_cookie
from app.security.sessions import RequiredAuth, clear_session_cookie
from app.usage import usage_for

router = APIRouter()


class PlanOut(BaseModel):
    tier: str  # free | paid
    name: str  # free | lifetime | pro_monthly | pro_yearly
    access_ends_at: datetime | None


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    avatar_url: str | None
    code_opt_in: bool
    created_at: datetime
    plan: PlanOut
    usage: UsageOut


class MeUpdate(BaseModel):
    code_opt_in: bool


def me_response(db: Session, redis: Redis, user: User, settings: Settings) -> MeResponse:
    plan = plan_for(db, user, settings)
    usage = usage_for(db, redis, user, plan)
    return MeResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        code_opt_in=user.code_opt_in,
        created_at=user.created_at,
        plan=PlanOut(tier=plan.tier, name=plan.name, access_ends_at=plan.access_ends_at),
        usage=UsageOut.model_validate(usage, from_attributes=True),
    )


@router.get("/me", response_model=MeResponse)
def get_me(
    auth: RequiredAuth,
    db: DbSession,
    redis: RedisClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> MeResponse:
    return me_response(db, redis, auth.user, settings)


@router.patch("/me", response_model=MeResponse, dependencies=[Depends(require_csrf)])
def update_me(
    body: MeUpdate,
    auth: RequiredAuth,
    db: DbSession,
    redis: RedisClient,
    settings: Annotated[Settings, Depends(get_settings)],
) -> MeResponse:
    auth.user.code_opt_in = body.code_opt_in
    db.commit()
    return me_response(db, redis, auth.user, settings)


@router.delete("/me", status_code=204, dependencies=[Depends(require_csrf)])
def delete_me(
    auth: RequiredAuth,
    response: Response,
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Delete the account and everything tied to it at once (section 11).

    Foreign keys cascade to sessions, OAuth accounts, drafts, submissions, progress, usage and
    our copy of subscriptions; billing records stay with the payment provider. A renewing Pro
    subscription must be canceled first so nobody is charged for a deleted account.
    """
    renewing = db.scalar(
        select(Subscription.id).where(
            Subscription.user_id == auth.user.id,
            Subscription.plan != "lifetime",
            Subscription.status.in_(("active", "past_due")),
        )
    )
    if renewing is not None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "subscription_active",
            "Cancel your Pro subscription in the billing portal first, then delete your account.",
        )
    db.delete(auth.user)
    db.commit()
    clear_session_cookie(response, settings)
    set_csrf_cookie(response, settings, issue_token(settings, ANONYMOUS))

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy import select

from app.billing.provider import PlanName, WebhookRejectedError, WebhookRetryError
from app.billing.registry import Provider
from app.billing.service import handle_webhook, offers, plan_on_sale
from app.config import Settings, get_settings
from app.db import DbSession
from app.errors import AppError
from app.models import Subscription
from app.plans import plan_for
from app.security.csrf import require_csrf
from app.security.sessions import OptionalAuth, RequiredAuth

router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


class PlansResponse(BaseModel):
    currency: str
    lifetime_price_cents: int | None
    lifetime_available: bool
    lifetime_remaining: int
    pro_enabled: bool
    pro_monthly_price_cents: int
    pro_yearly_price_cents: int
    payments_enabled: bool
    current_plan: str | None


class CheckoutRequest(BaseModel):
    plan: PlanName


class UrlResponse(BaseModel):
    url: str


@router.get("/billing/plans", response_model=PlansResponse)
def get_plans(db: DbSession, auth: OptionalAuth, settings: SettingsDep) -> PlansResponse:
    current = plan_for(db, auth.user, settings).name if auth else None
    return PlansResponse(
        **offers(db, settings).__dict__,
        payments_enabled=settings.payment_provider is not None,
        current_plan=current,
    )


@router.post("/billing/checkout", response_model=UrlResponse, dependencies=[Depends(require_csrf)])
def create_checkout(
    body: CheckoutRequest,
    db: DbSession,
    auth: RequiredAuth,
    provider: Provider,
    settings: SettingsDep,
) -> UrlResponse:
    reason = plan_on_sale(db, settings, body.plan)
    if reason:
        raise AppError(status.HTTP_409_CONFLICT, "plan_unavailable", reason)
    current = plan_for(db, auth.user, settings)
    if current.name == "lifetime":
        raise AppError(
            status.HTTP_409_CONFLICT,
            "already_lifetime",
            "You already have Lifetime, which includes everything.",
        )
    if current.paid and body.plan != "lifetime" and current.access_ends_at is None:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "already_subscribed",
            "You already have an active Pro subscription. Manage it from the account page.",
        )
    return UrlResponse(url=provider.create_checkout(auth.user, body.plan).url)


@router.get("/billing/portal", response_model=UrlResponse)
def billing_portal(db: DbSession, auth: RequiredAuth, provider: Provider) -> UrlResponse:
    has_billing = db.scalar(
        select(Subscription.id).where(Subscription.user_id == auth.user.id).limit(1)
    )
    if has_billing is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "no_billing",
            "You don't have a paid plan, so there's no billing to manage.",
        )
    return UrlResponse(url=provider.portal_url(auth.user))


@router.post("/webhooks/payments", status_code=200)
async def payment_webhook(
    request: Request, db: DbSession, provider: Provider
) -> dict[str, Literal["processed", "duplicate"]]:
    """Signature-checked and idempotent. Any failure returns 5xx so the provider retries."""
    body = await request.body()
    headers = {key.lower(): value for key, value in request.headers.items()}
    try:
        processed = handle_webhook(db, provider, headers, body)
    except WebhookRejectedError as exc:
        db.rollback()
        raise AppError(status.HTTP_400_BAD_REQUEST, "webhook_rejected", str(exc)) from exc
    except WebhookRetryError as exc:
        db.rollback()
        raise AppError(status.HTTP_503_SERVICE_UNAVAILABLE, "webhook_retry", str(exc)) from exc
    return {"status": "processed" if processed else "duplicate"}

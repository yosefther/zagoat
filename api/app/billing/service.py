"""Billing rules that don't depend on the provider (brief, section 10)."""

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.billing.provider import (
    PaymentProvider,
    PlanName,
    ProviderSubscription,
    WebhookRetryError,
)
from app.clock import utcnow
from app.config import Settings
from app.models import Subscription, User, WebhookEvent

log = logging.getLogger(__name__)


def lifetime_sold(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.plan == "lifetime", Subscription.status != "refunded")
        )
        or 0
    )


@dataclass(frozen=True)
class Offers:
    currency: str
    lifetime_price_cents: int | None
    lifetime_available: bool
    lifetime_remaining: int
    pro_enabled: bool
    pro_monthly_price_cents: int
    pro_yearly_price_cents: int


def offers(db: Session, settings: Settings) -> Offers:
    remaining = max(0, settings.lifetime_cap - lifetime_sold(db))
    return Offers(
        currency=settings.currency,
        lifetime_price_cents=settings.lifetime_price_cents,
        lifetime_available=settings.lifetime_price_cents is not None and remaining > 0,
        lifetime_remaining=remaining,
        pro_enabled=settings.pro_subscriptions_enabled,
        pro_monthly_price_cents=settings.pro_monthly_price_cents,
        pro_yearly_price_cents=settings.pro_yearly_price_cents,
    )


def plan_on_sale(db: Session, settings: Settings, plan: PlanName) -> str | None:
    """None if the plan can be bought now, otherwise why not."""
    if plan == "lifetime":
        if settings.lifetime_price_cents is None:
            return "Lifetime isn't on sale yet."
        if lifetime_sold(db) >= settings.lifetime_cap:
            return f"All {settings.lifetime_cap} Lifetime plans are sold."
        return None
    if not settings.pro_subscriptions_enabled:
        return "Pro subscriptions aren't available yet."
    return None


def apply_state(db: Session, provider: str, state: ProviderSubscription) -> Subscription | None:
    """Store the provider's current view of a subscription. Out-of-order events can't win,
    because we always save what the provider says now, not what the event said."""
    row = db.scalar(
        select(Subscription).where(
            Subscription.provider == provider, Subscription.provider_ref == state.ref
        )
    )
    if row is None:
        if db.get(User, state.user_id) is None:
            log.warning("subscription %s belongs to a deleted user; ignoring", state.ref)
            return None
        row = Subscription(provider=provider, provider_ref=state.ref, user_id=state.user_id)
        db.add(row)
    became_past_due = state.status == "past_due" and row.status != "past_due"
    row.plan = state.plan
    row.status = state.status
    row.current_period_end = state.current_period_end
    if state.status == "past_due":
        row.past_due_since = state.past_due_since or (
            utcnow() if became_past_due else row.past_due_since
        )
    else:
        row.past_due_since = None
    return row


def handle_webhook(
    db: Session, provider: PaymentProvider, headers: dict[str, str], body: bytes
) -> bool:
    """Verify, deduplicate and apply one webhook. Returns False for a repeated event.

    The event id and the subscription update commit together: if anything fails, both
    roll back and the provider's retry is processed instead of skipped.
    """
    provider.verify_webhook(headers, body)
    event = provider.parse_event(body)
    if db.get(WebhookEvent, event.id) is not None:
        return False
    record = WebhookEvent(provider_event_id=event.id, type=event.type)
    db.add(record)
    try:
        db.flush()
    except IntegrityError:  # A concurrent delivery of the same event won the race.
        db.rollback()
        return False
    state = provider.fetch_subscription(event.subscription_ref)
    if state is None:
        raise WebhookRetryError(f"provider has no subscription {event.subscription_ref} yet")
    apply_state(db, provider.name, state)
    record.processed_at = utcnow()
    db.commit()
    return True


@dataclass
class ReconcileReport:
    checked: int = 0
    fixed: list[str] = field(default_factory=list)
    expired: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def reconcile(db: Session, provider: PaymentProvider, settings: Settings) -> ReconcileReport:
    """Nightly: compare paying users with the provider and fix any drift (section 10)."""
    report = ReconcileReport()
    rows = db.scalars(
        select(Subscription).where(
            Subscription.provider == provider.name,
            Subscription.status.in_(("active", "past_due", "canceled")),
        )
    ).all()
    now = utcnow()
    for row in rows:
        report.checked += 1
        state = provider.fetch_subscription(row.provider_ref)
        if state is None:
            report.missing.append(row.provider_ref)
            continue
        before = (row.status, row.plan, row.current_period_end)
        apply_state(db, provider.name, state)
        if (row.status, row.plan, row.current_period_end) != before:
            report.fixed.append(row.provider_ref)
        # Access already ends by rule; this makes the stored status say so too.
        grace_over = (
            row.status == "past_due"
            and row.past_due_since is not None
            and now >= row.past_due_since + timedelta(days=settings.past_due_grace_days)
        )
        period_over = (
            row.status == "canceled"
            and row.current_period_end is not None
            and now >= row.current_period_end
        )
        if grace_over or period_over:
            row.status = "expired"
            report.expired.append(row.provider_ref)
    db.commit()
    return report

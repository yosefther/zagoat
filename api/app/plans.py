"""Plans and the paid-access rule (brief, section 8).

Paid access is computed from the subscriptions table on every request; there is no stored
flag. Plan definitions and limits come from config.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.config import Settings
from app.models import Subscription, User

Tier = Literal["free", "paid"]


@dataclass(frozen=True)
class Plan:
    tier: Tier
    name: str  # free | lifetime | pro_monthly | pro_yearly
    submits_per_day: int
    runs_per_hour: int
    # When paid access ends, if it will (canceled Pro, or past due within the grace period).
    access_ends_at: datetime | None = None

    @property
    def paid(self) -> bool:
        return self.tier == "paid"


def grants_access(sub: Subscription, settings: Settings, now: datetime) -> bool:
    """The section 8 access rule for one subscription."""
    if sub.plan == "lifetime":
        return sub.status not in ("refunded", "expired")
    if sub.status == "active":
        return True
    if sub.status == "past_due":
        started = sub.past_due_since or now
        return now < started + timedelta(days=settings.past_due_grace_days)
    if sub.status == "canceled":
        return sub.current_period_end is not None and now < sub.current_period_end
    return False


def access_ends_at(sub: Subscription, settings: Settings) -> datetime | None:
    if sub.plan == "lifetime" or sub.status == "active":
        return None
    if sub.status == "past_due" and sub.past_due_since:
        return sub.past_due_since + timedelta(days=settings.past_due_grace_days)
    return sub.current_period_end


def plan_for(db: Session, user: User | None, settings: Settings) -> Plan:
    free = Plan("free", "free", settings.free_submits_per_day, settings.free_runs_per_hour)
    if user is None:
        return free
    now = utcnow()
    subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
    granting = [sub for sub in subs if grants_access(sub, settings, now)]
    if not granting:
        return free
    # Lifetime wins over Pro; otherwise prefer the subscription that lasts longest.
    best = min(
        granting,
        key=lambda sub: (
            sub.plan != "lifetime",
            access_ends_at(sub, settings) is not None,
            -(access_ends_at(sub, settings) or now).timestamp(),
        ),
    )
    return Plan(
        "paid",
        best.plan,
        settings.paid_submits_per_day,
        settings.paid_runs_per_hour,
        access_ends_at(best, settings),
    )

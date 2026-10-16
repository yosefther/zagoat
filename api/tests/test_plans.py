"""Section 8 access rule, computed from the subscriptions table."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.clock import utcnow
from app.models import User
from app.plans import plan_for
from tests.conftest import give_subscription, make_settings

SETTINGS = make_settings()


def user(db: Session) -> User:
    row = User(email="plan@example.com")
    db.add(row)
    db.commit()
    return row


def tier(db: Session, u: User) -> str:
    return plan_for(db, u, SETTINGS).tier


def test_no_subscription_is_free(db: Session) -> None:
    u = user(db)
    plan = plan_for(db, u, SETTINGS)

    assert (plan.tier, plan.name, plan.submits_per_day, plan.runs_per_hour) == (
        "free",
        "free",
        10,
        30,
    )


def test_visitors_are_free(db: Session) -> None:
    assert plan_for(db, None, SETTINGS).tier == "free"


def test_lifetime_is_paid_with_no_end(db: Session) -> None:
    u = user(db)
    give_subscription(db, u, "lifetime", "active")

    plan = plan_for(db, u, SETTINGS)

    assert (plan.tier, plan.name, plan.access_ends_at) == ("paid", "lifetime", None)
    assert (plan.submits_per_day, plan.runs_per_hour) == (100, 120)


def test_refunded_lifetime_is_free(db: Session) -> None:
    u = user(db)
    give_subscription(db, u, "lifetime", "refunded")

    assert tier(db, u) == "free"


def test_active_pro_is_paid(db: Session) -> None:
    u = user(db)
    give_subscription(db, u, "pro_monthly", "active", period_end=utcnow() + timedelta(days=20))

    assert tier(db, u) == "paid"


def test_past_due_keeps_access_for_the_grace_period(db: Session) -> None:
    u = user(db)
    sub = give_subscription(db, u, "pro_monthly", "past_due", past_due_since=utcnow())

    plan = plan_for(db, u, SETTINGS)
    assert plan.tier == "paid"
    assert plan.access_ends_at == sub.past_due_since + timedelta(days=7)  # type: ignore[operator]

    sub.past_due_since = utcnow() - timedelta(days=7, seconds=1)
    db.commit()
    assert tier(db, u) == "free"


def test_canceled_keeps_access_until_period_end(db: Session) -> None:
    u = user(db)
    sub = give_subscription(
        db, u, "pro_yearly", "canceled", period_end=utcnow() + timedelta(days=3)
    )
    assert tier(db, u) == "paid"

    sub.current_period_end = utcnow() - timedelta(seconds=1)
    db.commit()
    assert tier(db, u) == "free"


def test_expired_and_refunded_pro_are_free(db: Session) -> None:
    u = user(db)
    give_subscription(db, u, "pro_monthly", "expired")
    give_subscription(db, u, "pro_yearly", "refunded")

    assert tier(db, u) == "free"


def test_lifetime_wins_over_a_canceling_pro(db: Session) -> None:
    u = user(db)
    give_subscription(db, u, "pro_monthly", "canceled", period_end=utcnow() + timedelta(days=3))
    give_subscription(db, u, "lifetime", "active")

    assert plan_for(db, u, SETTINGS).name == "lifetime"

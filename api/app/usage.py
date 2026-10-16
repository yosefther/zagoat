"""Daily Submit and hourly Run counters (brief, section 9)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from fastapi import status
from redis import Redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import ratelimit
from app.clock import utcnow
from app.errors import AppError
from app.models import Submission, UsageDaily, User
from app.plans import Plan

RUN_WINDOW_SECONDS = 3600


@dataclass(frozen=True)
class Usage:
    submits_used: int
    submits_limit: int
    submits_reset_at: datetime
    runs_used: int
    runs_limit: int
    runs_reset_at: datetime


def utc_day(moment: datetime) -> date:
    return moment.astimezone(UTC).date()


def next_utc_midnight(moment: datetime) -> datetime:
    return datetime.combine(utc_day(moment) + timedelta(days=1), time(0), tzinfo=UTC)


def submits_used(db: Session, user: User, day: date) -> int:
    row = db.get(UsageDaily, (user.id, day))
    return row.submits if row else 0


def usage_for(db: Session, redis: Redis, user: User, plan: Plan) -> Usage:
    now = utcnow()
    window_start = int(now.timestamp()) - int(now.timestamp()) % RUN_WINDOW_SECONDS
    return Usage(
        submits_used=submits_used(db, user, utc_day(now)),
        submits_limit=plan.submits_per_day,
        submits_reset_at=next_utc_midnight(now),
        runs_used=ratelimit.peek(redis, "runs", str(user.id), RUN_WINDOW_SECONDS),
        runs_limit=plan.runs_per_hour,
        runs_reset_at=datetime.fromtimestamp(window_start + RUN_WINDOW_SECONDS, UTC),
    )


def take_submit(db: Session, user: User, plan: Plan) -> None:
    """Count a Submit when it's queued, or refuse it if today's Submits are used up."""
    day = utc_day(utcnow())
    used = submits_used(db, user, day)
    if used >= plan.submits_per_day:
        upgrade = "" if plan.paid else " Lifetime and Pro raise the limit."
        raise AppError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "submit_limit",
            f"You've used all {plan.submits_per_day} Submits for today. They reset at 00:00 "
            f"UTC.{upgrade}",
            extra={
                "limit": plan.submits_per_day,
                "resets_at": next_utc_midnight(utcnow()).isoformat(),
            },
        )
    db.execute(
        insert(UsageDaily)
        .values(user_id=user.id, day=day, submits=1)
        .on_conflict_do_update(
            index_elements=[UsageDaily.user_id, UsageDaily.day],
            set_={"submits": UsageDaily.submits + 1},
        )
    )


def refund_submit(db: Session, submission: Submission) -> None:
    """Give back a counted Submit that ended in system_error (section 9)."""
    if not submission.counted:
        return
    row = db.scalar(
        select(UsageDaily).where(
            UsageDaily.user_id == submission.user_id,
            UsageDaily.day == utc_day(submission.created_at),
        )
    )
    if row and row.submits > 0:
        row.submits -= 1
    submission.counted = False


def take_run(redis: Redis, user: User, plan: Plan) -> None:
    """Count a Run, or refuse it if this hour's Runs are used up. Runs never use Submits."""
    window = ratelimit.hit(redis, "runs", str(user.id), plan.runs_per_hour, RUN_WINDOW_SECONDS)
    if not window.allowed:
        upgrade = "" if plan.paid else " Lifetime and Pro raise the limit."
        ratelimit.enforce(
            window,
            f"You've used all {plan.runs_per_hour} test runs for this hour. Try again in "
            f"{max(1, window.retry_after_seconds // 60)} minutes.{upgrade}",
        )

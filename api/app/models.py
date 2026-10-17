"""ORM models for every table in section 6 of the brief."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist"

    email: Mapped[str] = mapped_column(String(320), primary_key=True)
    source: Mapped[str | None] = mapped_column(String(64))
    consent: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    code_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    provider_user_id: Mapped[str] = mapped_column(String(255))

    user: Mapped[User] = relationship(back_populates="oauth_accounts")


class UserSession(Base):
    """A signed-in browser. The cookie holds a random token; only its SHA-256 is stored."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class Problem(Base):
    """Public parts of a task, synced from problems/<id>/ by `python -m app.problems sync`."""

    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(String(240))
    category: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[str] = mapped_column(String(8))
    est_minutes: Mapped[int] = mapped_column(Integer)
    access: Mapped[str] = mapped_column(String(8))
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_hash: Mapped[str] = mapped_column(String(64))
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    statement: Mapped[str] = mapped_column(Text)
    starter_files: Mapped[dict[str, str]] = mapped_column(JSONB)
    hints: Mapped[list[str]] = mapped_column(JSONB)
    walkthrough: Mapped[str | None] = mapped_column(Text)
    reference_files: Mapped[dict[str, str]] = mapped_column(JSONB)
    # Metric names and thresholds, shown next to results. Not secret.
    metrics: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Draft(Base):
    """The user's latest editor contents for a problem, saved by debounced autosave."""

    __tablename__ = "drafts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_id: Mapped[str] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    files: Mapped[dict[str, str]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Submission(Base):
    """One Run or Submit. Its id is the job id the browser polls."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[str] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"))
    problem_version: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(8))  # run | submit
    files: Mapped[dict[str, str]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(8), default="queued")  # queued | running | done
    verdict: Mapped[str | None] = mapped_column(String(16))
    tests_passed: Mapped[int | None] = mapped_column(Integer)
    tests_total: Mapped[int | None] = mapped_column(Integer)
    # message, per-test results, and (Run only) stdout and stderr.
    results: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    metrics: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    # Whether this Submit uses up one of today's Submits (refunded on system_error).
    counted: Mapped[bool] = mapped_column(Boolean, default=False)
    # Seconds on the optional timer when the user pressed Submit. Never affects the verdict.
    timer_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Progress(Base):
    """Where a user is on one problem. States only move forward (section 11)."""

    __tablename__ = "progress"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    problem_id: Mapped[str] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), primary_key=True
    )
    # not_started | in_progress | attempted | solved
    state: Mapped[str] = mapped_column(String(16), default="not_started")
    hints_revealed: Mapped[int] = mapped_column(Integer, default=0)
    first_submit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Timer reading at the most recent timed Submit.
    timer_seconds: Mapped[int | None] = mapped_column(Integer)


class UsageDaily(Base):
    """Submits used per UTC day (section 9)."""

    __tablename__ = "usage_daily"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    submits: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base):
    """A Pro subscription or Lifetime purchase, mirrored from the payment provider."""

    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("provider", "provider_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    provider_ref: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(16))  # pro_monthly | pro_yearly | lifetime
    # active | past_due | canceled | expired | refunded
    status: Mapped[str] = mapped_column(String(16))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the status last became past_due; the grace period counts from here.
    past_due_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WebhookEvent(Base):
    """Every payment webhook we accepted, so a repeated delivery is skipped (section 10)."""

    __tablename__ = "webhook_events"

    provider_event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

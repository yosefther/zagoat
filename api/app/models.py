"""ORM models for every table in section 6 of the brief."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
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

"""Server-side sessions in HTTP-only cookies."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.clock import utcnow
from app.config import Settings, get_settings
from app.db import DbSession
from app.errors import AppError
from app.models import User, UserSession


@dataclass(frozen=True)
class Auth:
    user: User
    session_id: str


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, settings: Settings, user: User) -> tuple[str, UserSession]:
    """Create a session row and return the raw cookie token with it."""
    token = secrets.token_urlsafe(32)
    row = UserSession(
        id=_hash(token),
        user_id=user.id,
        expires_at=utcnow() + timedelta(days=settings.session_lifetime_days),
    )
    db.add(row)
    db.flush()
    return token, row


def set_session_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_lifetime_days * 24 * 3600,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
        path="/",
    )


def end_session(db: Session, session_id: str) -> None:
    db.execute(delete(UserSession).where(UserSession.id == session_id))


def optional_auth(
    request: Request, db: DbSession, settings: Annotated[Settings, Depends(get_settings)]
) -> Auth | None:
    """Resolve the signed-in user from the session cookie, or None for visitors."""
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    row = db.scalar(
        select(UserSession)
        .options(joinedload(UserSession.user))
        .where(UserSession.id == _hash(token), UserSession.expires_at > utcnow())
    )
    if row is None:
        return None
    request.state.session_id = row.id
    return Auth(user=row.user, session_id=row.id)


def require_auth(auth: Annotated[Auth | None, Depends(optional_auth)]) -> Auth:
    if auth is None:
        raise AppError(status.HTTP_401_UNAUTHORIZED, "not_signed_in", "Sign in to continue.")
    return auth


OptionalAuth = Annotated[Auth | None, Depends(optional_auth)]
RequiredAuth = Annotated[Auth, Depends(require_auth)]

"""Signed double-submit CSRF tokens (section 13).

The API sets a readable `zagoat_csrf` cookie. The web app copies it into the
`X-CSRF-Token` header on every state-changing request. A request passes when the header
matches the cookie and the token's signature is valid for the caller's session, so a token
planted from another subdomain or issued to another session is rejected.
"""

import hashlib
import hmac
import secrets
from typing import Annotated

from fastapi import Depends, Request, Response, status

from app.config import Settings, get_settings
from app.errors import AppError
from app.security.sessions import OptionalAuth

ANONYMOUS = "anonymous"


def _sign(secret_key: str, binding: str, nonce: str) -> str:
    message = f"{binding}:{nonce}".encode()
    return hmac.new(secret_key.encode(), message, hashlib.sha256).hexdigest()


def issue_token(settings: Settings, binding: str = ANONYMOUS) -> str:
    nonce = secrets.token_urlsafe(24)
    return f"{nonce}.{_sign(settings.secret_key, binding, nonce)}"


def token_is_valid(settings: Settings, token: str, binding: str) -> bool:
    nonce, _, signature = token.partition(".")
    if not nonce or not signature:
        return False
    return hmac.compare_digest(signature, _sign(settings.secret_key, binding, nonce))


def set_csrf_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        max_age=settings.csrf_cookie_max_age_seconds,
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=False,  # The web app must read it to echo it in a header.
        samesite="lax",
        path="/",
    )


def csrf_binding(request: Request) -> str:
    """What the token is bound to: the session id when signed in, else ANONYMOUS."""
    session_id = getattr(request.state, "session_id", None)
    return str(session_id) if session_id else ANONYMOUS


def require_csrf(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    _auth: OptionalAuth,  # Resolves the session first, so the token's binding is known.
) -> None:
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get(settings.csrf_header_name)
    if (
        not cookie
        or not header
        or not hmac.compare_digest(cookie, header)
        or not token_is_valid(settings, header, csrf_binding(request))
    ):
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "csrf_failed",
            "Your security token is missing or out of date. Reload the page and try again.",
        )

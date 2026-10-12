import json
import secrets
from collections.abc import Iterator
from typing import Annotated
from urllib.parse import urlencode

import httpx2
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth.accounts import sign_in_with_profile
from app.auth.providers import OAuthError, Provider, enabled_providers
from app.config import Settings, get_settings
from app.db import DbSession
from app.ratelimit import client_ip, hit
from app.redis_client import RedisClient
from app.security.csrf import ANONYMOUS, issue_token, require_csrf, set_csrf_cookie
from app.security.sessions import (
    RequiredAuth,
    clear_session_cookie,
    create_session,
    end_session,
    set_session_cookie,
)

router = APIRouter(prefix="/auth")

STATE_COOKIE = "zagoat_oauth_state"


def get_oauth_http_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Iterator[httpx2.Client]:
    with httpx2.Client(timeout=settings.oauth_http_timeout_seconds) as client:
        yield client


def safe_return_path(value: str | None) -> str:
    """Only allow same-site relative paths, so sign-in can't redirect off zagoat."""
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value:
        return "/"
    return value


def _redirect_uri(settings: Settings, provider: str) -> str:
    return f"{settings.api_origin}/auth/{provider}/callback"


def _signin_error(settings: Settings, code: str) -> RedirectResponse:
    return RedirectResponse(f"{settings.web_origin}/signin?{urlencode({'error': code})}", 303)


class ProvidersResponse(BaseModel):
    providers: list[str]


@router.get("/providers", response_model=ProvidersResponse)
def list_providers(settings: Annotated[Settings, Depends(get_settings)]) -> ProvidersResponse:
    return ProvidersResponse(providers=list(enabled_providers(settings)))


@router.get("/{provider}/start")
def start_sign_in(
    provider: str,
    request: Request,
    redis: RedisClient,
    settings: Annotated[Settings, Depends(get_settings)],
    return_to: str | None = None,
) -> RedirectResponse:
    selected: Provider | None = enabled_providers(settings).get(provider)
    if selected is None:
        return _signin_error(settings, "provider_unavailable")
    if not hit(redis, "signin", client_ip(request), settings.ip_attempts_per_hour, 3600).allowed:
        return _signin_error(settings, "rate_limited")

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    redis.set(
        f"oauth:{state}",
        json.dumps(
            {"provider": provider, "verifier": verifier, "return_to": safe_return_path(return_to)}
        ),
        ex=settings.oauth_state_ttl_seconds,
    )
    response = RedirectResponse(
        selected.authorize_url(
            state=state, verifier=verifier, redirect_uri=_redirect_uri(settings, provider)
        ),
        303,
    )
    # Binds the flow to this browser, so a stolen callback link can't sign someone else in.
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=settings.oauth_state_ttl_seconds,
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
        path="/auth",
    )
    return response


@router.get("/{provider}/callback")
def finish_sign_in(
    provider: str,
    request: Request,
    db: DbSession,
    redis: RedisClient,
    settings: Annotated[Settings, Depends(get_settings)],
    http: Annotated[httpx2.Client, Depends(get_oauth_http_client)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    selected = enabled_providers(settings).get(provider)
    if selected is None:
        return _signin_error(settings, "provider_unavailable")
    if error:
        return _signin_error(settings, "access_denied")

    raw = redis.getdel(f"oauth:{state}") if state else None
    if not code or not state or raw is None or request.cookies.get(STATE_COOKIE) != state:
        return _signin_error(settings, "expired")
    flow = json.loads(raw)
    if flow["provider"] != provider:
        return _signin_error(settings, "expired")

    try:
        profile = selected.fetch_profile(
            http,
            code=code,
            verifier=flow["verifier"],
            redirect_uri=_redirect_uri(settings, provider),
        )
        user = sign_in_with_profile(db, provider, profile)
    except OAuthError as exc:
        db.rollback()
        return _signin_error(settings, exc.code)
    except httpx2.HTTPError:
        db.rollback()
        return _signin_error(settings, "provider_error")

    token, session = create_session(db, settings, user)
    db.commit()

    response = RedirectResponse(f"{settings.web_origin}{flow['return_to']}", 303)
    set_session_cookie(response, settings, token)
    set_csrf_cookie(response, settings, issue_token(settings, session.id))
    response.delete_cookie(STATE_COOKIE, path="/auth")
    return response


@router.post("/logout", status_code=204, dependencies=[Depends(require_csrf)])
def logout(
    auth: RequiredAuth,
    response: Response,
    db: DbSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    end_session(db, auth.session_id)
    db.commit()
    clear_session_cookie(response, settings)
    set_csrf_cookie(response, settings, issue_token(settings, ANONYMOUS))

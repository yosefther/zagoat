"""OAuth 2.0 authorization-code flow with PKCE for GitHub and Google.

Each provider builds its authorize URL, swaps the code for an access token and returns a
normalized profile. A development-only provider runs the same flow without leaving the API.
"""

import base64
import hashlib
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

import httpx2

from app.config import Environment, Settings


class OAuthError(Exception):
    """Sign-in failed. `code` is shown to the web app as /signin?error=<code>."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Profile:
    provider_user_id: str
    email: str | None
    email_verified: bool
    name: str | None
    avatar_url: str | None


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class Provider(Protocol):
    @property
    def name(self) -> str: ...

    def authorize_url(self, *, state: str, verifier: str, redirect_uri: str) -> str: ...

    def fetch_profile(
        self, client: httpx2.Client, *, code: str, verifier: str, redirect_uri: str
    ) -> Profile: ...


def _json(response: httpx2.Response) -> Any:
    if response.status_code >= 400:
        raise OAuthError("provider_error")
    try:
        return response.json()
    except ValueError as exc:
        raise OAuthError("provider_error") from exc


@dataclass(frozen=True)
class GitHubProvider:
    client_id: str
    client_secret: str
    name: str = "github"

    def authorize_url(self, *, state: str, verifier: str, redirect_uri: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "scope": "read:user user:email",
                "state": state,
                "code_challenge": code_challenge(verifier),
                "code_challenge_method": "S256",
                "allow_signup": "true",
            }
        )
        return f"https://github.com/login/oauth/authorize?{query}"

    def fetch_profile(
        self, client: httpx2.Client, *, code: str, verifier: str, redirect_uri: str
    ) -> Profile:
        token = _json(
            client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": verifier,
                },
                headers={"Accept": "application/json"},
            )
        )
        access_token = token.get("access_token")
        if not access_token:
            raise OAuthError("provider_error")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        user = _json(client.get("https://api.github.com/user", headers=headers))
        emails = _json(client.get("https://api.github.com/user/emails", headers=headers))
        primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
        return Profile(
            provider_user_id=str(user["id"]),
            email=primary["email"] if primary else None,
            email_verified=primary is not None,
            name=user.get("name") or user.get("login"),
            avatar_url=user.get("avatar_url"),
        )


@dataclass(frozen=True)
class GoogleProvider:
    client_id: str
    client_secret: str
    name: str = "google"

    def authorize_url(self, *, state: str, verifier: str, redirect_uri: str) -> str:
        query = urlencode(
            {
                "client_id": self.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "code_challenge": code_challenge(verifier),
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    def fetch_profile(
        self, client: httpx2.Client, *, code: str, verifier: str, redirect_uri: str
    ) -> Profile:
        token = _json(
            client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "code_verifier": verifier,
                },
            )
        )
        access_token = token.get("access_token")
        if not access_token:
            raise OAuthError("provider_error")
        info = _json(
            client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        )
        return Profile(
            provider_user_id=str(info["sub"]),
            email=info.get("email"),
            email_verified=bool(info.get("email_verified")),
            name=info.get("name"),
            avatar_url=info.get("picture"),
        )


@dataclass(frozen=True)
class DevProvider:
    """Local development only: the "code" is the email to sign in as."""

    name: str = "dev"

    def authorize_url(self, *, state: str, verifier: str, redirect_uri: str) -> str:
        return f"{redirect_uri}?{urlencode({'state': state, 'code': 'dev@example.com'})}"

    def fetch_profile(
        self, client: httpx2.Client, *, code: str, verifier: str, redirect_uri: str
    ) -> Profile:
        return Profile(
            provider_user_id=code,
            email=code,
            email_verified=True,
            name="Dev User",
            avatar_url=None,
        )


def enabled_providers(settings: Settings) -> dict[str, Provider]:
    providers: dict[str, Provider] = {}
    if settings.github_client_id and settings.github_client_secret:
        providers["github"] = GitHubProvider(
            settings.github_client_id, settings.github_client_secret
        )
    if settings.google_client_id and settings.google_client_secret:
        providers["google"] = GoogleProvider(
            settings.google_client_id, settings.google_client_secret
        )
    if settings.dev_login_enabled and settings.environment is not Environment.PRODUCTION:
        providers["dev"] = DevProvider()
    return providers

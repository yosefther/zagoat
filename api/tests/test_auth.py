import json
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import OAuthAccount, User, UserSession
from app.routes.auth import get_oauth_http_client, safe_return_path
from tests.conftest import csrf_headers, make_settings, sign_in

Handler = Callable[[httpx2.Request], httpx2.Response]


def github_api(
    user_id: int = 42,
    emails: list[dict[str, Any]] | None = None,
    token_status: int = 200,
) -> Handler:
    if emails is None:
        emails = [{"email": "Ada@Example.com", "primary": True, "verified": True}]

    def handler(request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        if url == "https://github.com/login/oauth/access_token":
            body = parse_qs(request.content.decode())
            assert body["code"] == ["the-code"]
            assert body["code_verifier"][0]
            return httpx2.Response(token_status, json={"access_token": "gh-token"})
        assert request.headers["Authorization"] == "Bearer gh-token"
        if url == "https://api.github.com/user":
            return httpx2.Response(
                200, json={"id": user_id, "login": "ada", "name": None, "avatar_url": "https://a/1"}
            )
        if url == "https://api.github.com/user/emails":
            return httpx2.Response(200, json=emails)
        raise AssertionError(f"unexpected request {url}")

    return handler


def google_api(email_verified: bool = True) -> Handler:
    def handler(request: httpx2.Request) -> httpx2.Response:
        url = str(request.url)
        if url == "https://oauth2.googleapis.com/token":
            return httpx2.Response(200, json={"access_token": "g-token"})
        if url == "https://openidconnect.googleapis.com/v1/userinfo":
            return httpx2.Response(
                200,
                json={
                    "sub": "g-7",
                    "email": "ada@example.com",
                    "email_verified": email_verified,
                    "name": "Ada Lovelace",
                    "picture": "https://g/1",
                },
            )
        raise AssertionError(f"unexpected request {url}")

    return handler


@pytest.fixture
def settings() -> Settings:
    return make_settings(
        github_client_id="gh-id",
        github_client_secret="gh-secret",
        google_client_id="g-id",
        google_client_secret="g-secret",
        api_origin="http://api.test",
    )


@pytest.fixture
def use_provider_api(app: FastAPI) -> Callable[[Handler], None]:
    def install(handler: Handler) -> None:
        def client() -> Any:
            with httpx2.Client(transport=httpx2.MockTransport(handler)) as c:
                yield c

        app.dependency_overrides[get_oauth_http_client] = client

    return install


def start(client: TestClient, provider: str, return_to: str = "/problems") -> str:
    response = client.get(
        f"/auth/{provider}/start", params={"return_to": return_to}, follow_redirects=False
    )
    assert response.status_code == 303
    query = parse_qs(urlparse(response.headers["location"]).query)
    return query["state"][0]


def callback(client: TestClient, provider: str, state: str, code: str = "the-code") -> str:
    response = client.get(
        f"/auth/{provider}/callback",
        params={"code": code, "state": state},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return str(response.headers["location"])


def test_providers_lists_only_configured_ones(client: TestClient) -> None:
    assert client.get("/auth/providers").json() == {"providers": ["github", "google"]}


def test_github_start_redirects_with_pkce_and_state(client: TestClient) -> None:
    response = client.get("/auth/github/start", follow_redirects=False)

    location = urlparse(response.headers["location"])
    query = parse_qs(location.query)
    assert location.netloc == "github.com"
    assert query["redirect_uri"] == ["http://api.test/auth/github/callback"]
    assert query["code_challenge_method"] == ["S256"]
    assert response.cookies["zagoat_oauth_state"] == query["state"][0]


def test_github_sign_in_creates_user_and_session(
    client: TestClient, db: Session, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())

    location = callback(client, "github", start(client, "github", "/problems/rag-1"))

    assert location == "http://localhost:3000/problems/rag-1"
    user = db.scalars(select(User)).one()
    assert (user.email, user.name, user.avatar_url) == ("ada@example.com", "ada", "https://a/1")
    assert user.oauth_accounts[0].provider_user_id == "42"
    assert client.cookies.get("zagoat_session")
    me = client.get("/me").json()
    assert me["email"] == "ada@example.com"
    assert me["code_opt_in"] is False


def test_sign_in_sets_http_only_session_cookie(
    client: TestClient, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    state = start(client, "github")

    response = client.get(
        "/auth/github/callback",
        params={"code": "the-code", "state": state},
        follow_redirects=False,
    )

    cookies = [c.lower() for c in response.headers.get_list("set-cookie")]
    session_cookie = next(c for c in cookies if c.startswith("zagoat_session="))
    assert "httponly" in session_cookie
    assert "samesite=lax" in session_cookie


def test_returning_user_signs_in_to_same_account(
    client: TestClient, db: Session, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    callback(client, "github", start(client, "github"))
    callback(client, "github", start(client, "github"))

    assert db.scalar(select(func.count()).select_from(User)) == 1
    assert db.scalar(select(func.count()).select_from(UserSession)) == 2


def test_google_links_to_existing_user_with_same_verified_email(
    client: TestClient, db: Session, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    callback(client, "github", start(client, "github"))
    use_provider_api(google_api())

    callback(client, "google", start(client, "google"))

    user = db.scalars(select(User)).one()
    assert sorted(a.provider for a in user.oauth_accounts) == ["github", "google"]


def test_unverified_email_is_refused(
    client: TestClient, db: Session, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(google_api(email_verified=False))

    location = callback(client, "google", start(client, "google"))

    assert location == "http://localhost:3000/signin?error=email_unverified"
    assert db.scalars(select(User)).all() == []


def test_github_without_verified_primary_email_is_refused(
    client: TestClient, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(
        github_api(emails=[{"email": "a@example.com", "primary": True, "verified": False}])
    )

    location = callback(client, "github", start(client, "github"))

    assert location.endswith("error=email_unverified")


def test_provider_failure_redirects_with_error(
    client: TestClient, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api(token_status=500))

    assert callback(client, "github", start(client, "github")).endswith("error=provider_error")


def test_callback_rejects_unknown_state(client: TestClient) -> None:
    start(client, "github")

    assert callback(client, "github", "made-up-state").endswith("error=expired")


def test_callback_rejects_state_from_another_browser(
    client: TestClient, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    state = start(client, "github")
    client.cookies.delete("zagoat_oauth_state", path="/auth")
    client.cookies.clear()

    assert callback(client, "github", state).endswith("error=expired")


def test_state_can_be_used_only_once(
    client: TestClient, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    state = start(client, "github")
    callback(client, "github", state)
    client.cookies.set("zagoat_oauth_state", state, path="/auth")

    assert callback(client, "github", state).endswith("error=expired")


def test_user_denying_access_redirects_with_error(client: TestClient) -> None:
    response = client.get(
        "/auth/github/callback", params={"error": "access_denied"}, follow_redirects=False
    )

    assert response.headers["location"].endswith("error=access_denied")


def test_unconfigured_provider_is_unavailable(client: TestClient) -> None:
    response = client.get("/auth/dev/start", follow_redirects=False)

    assert response.headers["location"].endswith("error=provider_unavailable")


def test_sign_in_attempts_are_rate_limited_per_ip(client: TestClient) -> None:
    for _ in range(5):
        start(client, "github")

    response = client.get("/auth/github/start", follow_redirects=False)

    assert response.headers["location"].endswith("error=rate_limited")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/problems", "/problems"),
        (None, "/"),
        ("https://evil.example", "/"),
        ("//evil.example", "/"),
        ("/\\evil.example", "/"),
    ],
)
def test_return_path_stays_on_site(value: str | None, expected: str) -> None:
    assert safe_return_path(value) == expected


def test_dev_login_works_only_when_enabled(db: Session, redis: Any) -> None:
    from app.db import get_db
    from app.main import create_app

    app = create_app(make_settings(dev_login_enabled=True))
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    location = callback(client, "dev", start(client, "dev"), code="dev@example.com")

    assert location == "http://localhost:3000/problems"
    assert client.get("/me").json()["email"] == "dev@example.com"


def test_me_requires_sign_in(client: TestClient) -> None:
    response = client.get("/me")

    assert response.status_code == 401
    assert response.json()["error"] == {"code": "not_signed_in", "message": "Sign in to continue."}


def test_expired_session_is_ignored(client: TestClient, db: Session) -> None:
    from datetime import timedelta

    sign_in(client, db)
    session = db.scalars(select(UserSession)).one()
    session.expires_at = session.expires_at - timedelta(days=60)
    db.commit()

    assert client.get("/me").status_code == 401


def test_logout_ends_the_session(client: TestClient, db: Session) -> None:
    sign_in(client, db)
    headers = csrf_headers(client)

    response = client.post("/auth/logout", headers=headers)

    assert response.status_code == 204
    assert db.scalars(select(UserSession)).all() == []
    assert client.get("/me").status_code == 401


def test_csrf_token_issued_before_sign_in_is_rejected_after(
    client: TestClient, db: Session
) -> None:
    anonymous_headers = csrf_headers(client)
    sign_in(client, db)

    response = client.post("/auth/logout", headers=anonymous_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_code_opt_in_can_be_changed(client: TestClient, db: Session) -> None:
    sign_in(client, db)

    response = client.patch("/me", json={"code_opt_in": True}, headers=csrf_headers(client))

    assert response.status_code == 200
    assert response.json()["code_opt_in"] is True


def test_delete_me_removes_user_and_related_rows(
    client: TestClient, db: Session, use_provider_api: Callable[[Handler], None]
) -> None:
    use_provider_api(github_api())
    callback(client, "github", start(client, "github"))
    other = sign_in(TestClient(client.app), db, email="other@example.com")

    response = client.delete("/me", headers=csrf_headers(client))

    assert response.status_code == 204
    assert db.scalars(select(User)).all() == [other]
    assert db.scalars(select(OAuthAccount)).all() == []
    assert [s.user_id for s in db.scalars(select(UserSession))] == [other.id]
    assert client.get("/me").status_code == 401


def test_oauth_state_is_stored_with_ttl(client: TestClient, redis: Any) -> None:
    state = start(client, "github", "/account")

    stored = json.loads(redis.get(f"oauth:{state}"))
    assert stored["provider"] == "github"
    assert stored["return_to"] == "/account"
    assert 0 < redis.ttl(f"oauth:{state}") <= 600

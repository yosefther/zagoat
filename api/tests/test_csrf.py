from fastapi.testclient import TestClient

from app.config import Settings
from app.security.csrf import issue_token, token_is_valid
from tests.conftest import csrf_headers

VALID_BODY = {"email": "ada@example.com", "consent": True}


def test_csrf_endpoint_sets_a_readable_cookie(client: TestClient) -> None:
    response = client.get("/csrf")

    token = response.json()["csrf_token"]
    assert response.cookies["zagoat_csrf"] == token
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" not in set_cookie
    assert "samesite=lax" in set_cookie


def test_state_changing_route_rejects_missing_token(client: TestClient) -> None:
    response = client.post("/waitlist", json=VALID_BODY)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_state_changing_route_rejects_header_that_differs_from_cookie(client: TestClient) -> None:
    client.get("/csrf")
    response = client.post("/waitlist", json=VALID_BODY, headers={"X-CSRF-Token": "forged.token"})

    assert response.status_code == 403


def test_state_changing_route_rejects_unsigned_token_even_if_cookie_matches(
    client: TestClient,
) -> None:
    client.cookies.set("zagoat_csrf", "planted.value")
    response = client.post("/waitlist", json=VALID_BODY, headers={"X-CSRF-Token": "planted.value"})

    assert response.status_code == 403


def test_state_changing_route_accepts_matching_signed_token(client: TestClient) -> None:
    response = client.post("/waitlist", json=VALID_BODY, headers=csrf_headers(client))

    assert response.status_code == 200


def test_tokens_are_bound_to_their_session(settings: Settings) -> None:
    token = issue_token(settings, "session-a")

    assert token_is_valid(settings, token, "session-a")
    assert not token_is_valid(settings, token, "session-b")
    assert not token_is_valid(settings, token, "anonymous")

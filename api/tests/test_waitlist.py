from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WaitlistEntry
from tests.conftest import csrf_headers


def test_join_waitlist_stores_normalized_email(client: TestClient, db: Session) -> None:
    response = client.post(
        "/waitlist",
        json={"email": "Ada@Example.com", "consent": True, "source": "landing"},
        headers=csrf_headers(client),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "joined"}
    entry = db.scalars(select(WaitlistEntry)).one()
    assert (entry.email, entry.source, entry.consent) == ("ada@example.com", "landing", True)


def test_joining_twice_succeeds_without_duplicates(client: TestClient, db: Session) -> None:
    headers = csrf_headers(client)
    for email in ("ada@example.com", "ADA@example.com"):
        response = client.post("/waitlist", json={"email": email, "consent": True}, headers=headers)
        assert response.status_code == 200

    assert len(db.scalars(select(WaitlistEntry)).all()) == 1


def test_consent_is_required(client: TestClient, db: Session) -> None:
    response = client.post(
        "/waitlist",
        json={"email": "ada@example.com", "consent": False},
        headers=csrf_headers(client),
    )

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "invalid_request"
    assert "Tick the box" in body["fields"]["consent"]
    assert db.scalars(select(WaitlistEntry)).all() == []


def test_invalid_email_is_rejected_with_field_error(client: TestClient) -> None:
    response = client.post(
        "/waitlist",
        json={"email": "not-an-email", "consent": True},
        headers=csrf_headers(client),
    )

    assert response.status_code == 422
    assert "email" in response.json()["error"]["fields"]


def test_waitlist_is_rate_limited_per_ip(client: TestClient) -> None:
    headers = csrf_headers(client)
    for i in range(5):
        response = client.post(
            "/waitlist", json={"email": f"user{i}@example.com", "consent": True}, headers=headers
        )
        assert response.status_code == 200

    response = client.post(
        "/waitlist", json={"email": "user6@example.com", "consent": True}, headers=headers
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert int(response.headers["Retry-After"]) > 0

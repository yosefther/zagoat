"""Section 10: checkout, webhooks, subscription states, Lifetime cap, reconciliation."""

import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.fake import FakeProvider
from app.billing.provider import ProviderSubscription
from app.billing.service import reconcile
from app.clock import utcnow
from app.config import Settings
from app.db import get_db
from app.main import create_app
from app.models import Subscription, User, WebhookEvent
from tests.conftest import csrf_headers, give_subscription, make_settings, sign_in
from tests.problem_factory import add_problem


@pytest.fixture
def settings() -> Settings:
    return make_settings(lifetime_price_cents=14900, pro_subscriptions_enabled=True)


@pytest.fixture
def fake(settings: Settings, redis: Redis) -> FakeProvider:
    return FakeProvider(settings, redis)


@pytest.fixture
def user(client: TestClient, db: Session) -> User:
    add_problem(db, "paid-01", access="paid")
    return sign_in(client, db)


def checkout(client: TestClient, plan: str) -> str:
    response = client.post("/billing/checkout", json={"plan": plan}, headers=csrf_headers(client))
    assert response.status_code == 200, response.text
    return str(response.json()["url"])


def buy(client: TestClient, plan: str) -> Subscription:
    """Run the fake hosted checkout end to end."""
    session = checkout(client, plan).rsplit("/", 1)[-1]
    done = client.post(f"/billing/fake/checkout/{session}/complete", follow_redirects=False)
    assert done.status_code == 303
    assert done.headers["location"] == "http://localhost:3000/account?checkout=success"
    db: Session = client.app.dependency_overrides[get_db]()  # type: ignore[attr-defined]
    return db.scalars(select(Subscription).order_by(Subscription.id.desc())).first()  # type: ignore[return-value]


def portal(client: TestClient, ref: str, action: str) -> None:
    response = client.post(
        f"/billing/fake/portal/{ref}", data={"action": action}, follow_redirects=False
    )
    assert response.status_code == 303


def plan_name(client: TestClient) -> str:
    return str(client.get("/me").json()["plan"]["name"])


def test_plans_show_offers(client: TestClient) -> None:
    body = client.get("/billing/plans").json()

    assert body["lifetime_available"] is True
    assert body["lifetime_price_cents"] == 14900
    assert body["lifetime_remaining"] == 100
    assert body["pro_enabled"] is True
    assert body["current_plan"] is None


def test_lifetime_is_not_sold_without_a_price(db: Session, redis: Redis) -> None:
    app = create_app(make_settings())
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    sign_in(client, db)

    assert client.get("/billing/plans").json()["lifetime_available"] is False
    response = client.post(
        "/billing/checkout", json={"plan": "lifetime"}, headers=csrf_headers(client)
    )
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "Lifetime isn't on sale yet."


def test_pro_is_behind_the_feature_flag(db: Session, redis: Redis) -> None:
    app = create_app(make_settings(lifetime_price_cents=100))
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    sign_in(client, db)

    response = client.post(
        "/billing/checkout", json={"plan": "pro_monthly"}, headers=csrf_headers(client)
    )

    assert response.status_code == 409
    assert "Pro subscriptions aren't available yet" in response.json()["error"]["message"]
    assert client.get("/billing/plans").json()["pro_enabled"] is False


def test_lifetime_purchase_unlocks_paid_features(client: TestClient, user: User) -> None:
    sub = buy(client, "lifetime")

    assert (sub.plan, sub.status, sub.current_period_end) == ("lifetime", "active", None)
    assert plan_name(client) == "lifetime"
    assert client.get("/problems/paid-01").json()["lock"] is None
    assert client.get("/problems/paid-01/walkthrough").status_code == 200


def test_subscription_lifecycle(client: TestClient, user: User, db: Session) -> None:
    sub = buy(client, "pro_monthly")
    assert sub.status == "active" and sub.current_period_end is not None
    first_end = sub.current_period_end

    portal(client, sub.provider_ref, "renew")
    db.refresh(sub)
    assert sub.status == "active" and sub.current_period_end > first_end

    portal(client, sub.provider_ref, "fail")
    db.refresh(sub)
    assert sub.status == "past_due" and sub.past_due_since is not None
    assert plan_name(client) == "pro_monthly"  # grace period

    portal(client, sub.provider_ref, "resume")
    portal(client, sub.provider_ref, "cancel")
    db.refresh(sub)
    assert sub.status == "canceled"
    assert plan_name(client) == "pro_monthly"  # until the period ends

    portal(client, sub.provider_ref, "end")
    db.refresh(sub)
    assert sub.status == "expired"
    assert plan_name(client) == "free"


def test_refund_removes_access_at_once(client: TestClient, user: User, db: Session) -> None:
    sub = buy(client, "lifetime")

    portal(client, sub.provider_ref, "refund")

    db.refresh(sub)
    assert sub.status == "refunded"
    assert plan_name(client) == "free"


def test_webhooks_need_a_valid_signature(client: TestClient, fake: FakeProvider) -> None:
    _, body = fake.signed_event("checkout.completed", "sub_x")

    response = client.post(
        "/webhooks/payments", content=body, headers={"x-fake-signature": "sha256=0"}
    )

    assert response.status_code == 400


def save_sub(fake: FakeProvider, user: User, status: str, **extra: object) -> ProviderSubscription:
    sub = ProviderSubscription(
        ref="sub_test",
        user_id=user.id,
        plan="pro_monthly",
        status=status,  # type: ignore[arg-type]
        current_period_end=utcnow() + timedelta(days=10),
        **extra,  # type: ignore[arg-type]
    )
    fake.save(sub)
    return sub


def send(client: TestClient, headers: dict[str, str], body: bytes) -> dict[str, str]:
    response = client.post("/webhooks/payments", content=body, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_repeated_events_are_skipped(
    client: TestClient, user: User, fake: FakeProvider, db: Session
) -> None:
    save_sub(fake, user, "active")
    headers, body = fake.signed_event("checkout.completed", "sub_test")

    assert send(client, headers, body) == {"status": "processed"}
    save_sub(fake, user, "canceled")
    assert send(client, headers, body) == {"status": "duplicate"}

    assert db.scalars(select(Subscription)).one().status == "active"
    assert len(db.scalars(select(WebhookEvent)).all()) == 1


def test_out_of_order_events_store_the_providers_current_state(
    client: TestClient, user: User, fake: FakeProvider, db: Session
) -> None:
    save_sub(fake, user, "canceled")

    # A late "resumed" event arrives after the user canceled.
    send(client, *fake.signed_event("subscription.resume", "sub_test"))

    assert db.scalars(select(Subscription)).one().status == "canceled"


def test_failed_processing_is_retried(
    client: TestClient, user: User, fake: FakeProvider, db: Session
) -> None:
    headers, body = fake.signed_event("checkout.completed", "sub_test")

    first = client.post("/webhooks/payments", content=body, headers=headers)
    assert first.status_code == 503
    assert db.scalars(select(WebhookEvent)).all() == []

    save_sub(fake, user, "active")
    assert send(client, headers, body) == {"status": "processed"}


def test_lifetime_cap(db: Session, redis: Redis) -> None:
    settings = make_settings(lifetime_price_cents=14900, lifetime_cap=2)
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    buyer = sign_in(client, db)
    early_session = checkout(client, "lifetime").rsplit("/", 1)[-1]
    for i in range(2):
        other = User(email=f"buyer{i}@example.com")
        db.add(other)
        db.commit()
        give_subscription(db, other, "lifetime")

    assert client.get("/billing/plans").json()["lifetime_available"] is False
    sold_out = client.post(
        "/billing/checkout", json={"plan": "lifetime"}, headers=csrf_headers(client)
    )
    assert sold_out.status_code == 409
    assert "All 2 Lifetime plans are sold" in sold_out.json()["error"]["message"]

    # A checkout started before the cap was reached is still honored.
    client.post(f"/billing/fake/checkout/{early_session}/complete")
    assert plan_name(client) == "lifetime"
    assert db.scalars(select(Subscription).where(Subscription.user_id == buyer.id)).one()


def test_cannot_buy_twice(client: TestClient, user: User) -> None:
    buy(client, "lifetime")

    response = client.post(
        "/billing/checkout", json={"plan": "pro_yearly"}, headers=csrf_headers(client)
    )

    assert response.json()["error"]["code"] == "already_lifetime"


def test_portal_is_for_paying_users(client: TestClient, user: User) -> None:
    assert client.get("/billing/portal").status_code == 404

    buy(client, "pro_monthly")

    assert client.get("/billing/portal").json() == {
        "url": "http://localhost:8000/billing/fake/portal"
    }


def test_account_deletion_waits_for_pro_to_be_canceled(
    client: TestClient, user: User, db: Session
) -> None:
    sub = buy(client, "pro_monthly")

    blocked = client.delete("/me", headers=csrf_headers(client))
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "subscription_active"

    portal(client, sub.provider_ref, "cancel")
    assert client.delete("/me", headers=csrf_headers(client)).status_code == 204


def test_reconcile_fixes_drift_and_expires(
    user: User,
    fake: FakeProvider,
    db: Session,
    settings: Settings,
    freeze: Callable[[datetime], None],
) -> None:
    drifted = give_subscription(db, user, "pro_monthly", "active")
    drifted.provider_ref = "sub_test"
    db.commit()
    save_sub(fake, user, "canceled")
    lapsed = give_subscription(
        db, user, "pro_yearly", "past_due", past_due_since=utcnow() - timedelta(days=8)
    )
    fake.save(
        ProviderSubscription(
            lapsed.provider_ref, user.id, "pro_yearly", "past_due", None, lapsed.past_due_since
        )
    )
    gone = give_subscription(db, user, "pro_monthly", "active")

    report = reconcile(db, fake, settings)

    assert report.checked == 3
    assert report.fixed == ["sub_test"]
    assert report.expired == [lapsed.provider_ref]
    assert report.missing == [gone.provider_ref]
    db.refresh(drifted)
    db.refresh(lapsed)
    assert (drifted.status, lapsed.status) == ("canceled", "expired")


def test_payments_unavailable_without_a_provider(db: Session, redis: Redis) -> None:
    app: FastAPI = create_app(make_settings(payment_provider=None, lifetime_price_cents=100))
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    sign_in(client, db)

    response = client.post(
        "/billing/checkout", json={"plan": "lifetime"}, headers=csrf_headers(client)
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "payments_unavailable"
    assert client.get("/billing/plans").json()["payments_enabled"] is False
    assert client.get("/billing/fake/portal").status_code == 404


def test_webhook_for_a_deleted_user_is_ignored(
    client: TestClient, fake: FakeProvider, db: Session
) -> None:
    fake.save(ProviderSubscription("sub_gone", uuid.uuid4(), "lifetime", "active", None))

    send(client, *fake.signed_event("checkout.completed", "sub_gone"))

    assert db.scalars(select(Subscription)).all() == []

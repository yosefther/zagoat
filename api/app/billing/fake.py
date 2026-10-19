"""FakeProvider: a stand-in payment provider for local development and tests.

Its state lives in Redis, so the checkout and portal pages in `app/routes/fake_billing.py`
can change it the way a real provider would, then deliver signed webhooks.
"""

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime
from typing import Any

from redis import Redis

from app.billing.provider import (
    Checkout,
    PlanName,
    ProviderEvent,
    ProviderSubscription,
    WebhookRejectedError,
)
from app.config import Settings
from app.models import User

SIGNATURE_HEADER = "x-fake-signature"
CHECKOUT_TTL_SECONDS = 3600


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


class FakeProvider:
    name = "fake"

    def __init__(self, settings: Settings, redis: Redis) -> None:
        self.settings = settings
        self.redis = redis

    # PaymentProvider -------------------------------------------------------------------

    def create_checkout(self, user: User, plan: PlanName) -> Checkout:
        session = secrets.token_urlsafe(16)
        self.redis.set(
            f"fakepay:checkout:{session}",
            json.dumps({"user_id": str(user.id), "plan": plan}),
            ex=CHECKOUT_TTL_SECONDS,
        )
        return Checkout(url=f"{self.settings.api_origin}/billing/fake/checkout/{session}")

    def portal_url(self, user: User) -> str:
        return f"{self.settings.api_origin}/billing/fake/portal"

    def verify_webhook(self, headers: dict[str, str], body: bytes) -> None:
        given = headers.get(SIGNATURE_HEADER, "")
        if not hmac.compare_digest(given, sign(self.settings.payment_webhook_secret, body)):
            raise WebhookRejectedError("bad signature")

    def parse_event(self, payload: bytes) -> ProviderEvent:
        try:
            data = json.loads(payload)
            return ProviderEvent(
                id=str(data["id"]),
                type=str(data["type"]),
                subscription_ref=str(data["subscription"]),
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise WebhookRejectedError("malformed event") from exc

    def fetch_subscription(self, ref: str) -> ProviderSubscription | None:
        raw = self.redis.get(f"fakepay:sub:{ref}")
        if raw is None:
            return None
        data = json.loads(raw)
        return ProviderSubscription(
            ref=data["ref"],
            user_id=uuid.UUID(data["user_id"]),
            plan=data["plan"],
            status=data["status"],
            current_period_end=_date(data.get("current_period_end")),
            past_due_since=_date(data.get("past_due_since")),
        )

    # Fake-only helpers used by the dev pages and tests ----------------------------------

    def pending_checkout(self, session: str) -> dict[str, Any] | None:
        raw = self.redis.get(f"fakepay:checkout:{session}")
        return json.loads(raw) if raw else None

    def close_checkout(self, session: str) -> None:
        self.redis.delete(f"fakepay:checkout:{session}")

    def save(self, sub: ProviderSubscription) -> None:
        self.redis.set(
            f"fakepay:sub:{sub.ref}",
            json.dumps(
                {
                    "ref": sub.ref,
                    "user_id": str(sub.user_id),
                    "plan": sub.plan,
                    "status": sub.status,
                    "current_period_end": _iso(sub.current_period_end),
                    "past_due_since": _iso(sub.past_due_since),
                }
            ),
        )
        self.redis.sadd(f"fakepay:user:{sub.user_id}", sub.ref)

    def subscriptions_for(self, user_id: uuid.UUID) -> list[ProviderSubscription]:
        refs = sorted(r.decode() for r in self.redis.smembers(f"fakepay:user:{user_id}"))  # type: ignore[union-attr]
        return [sub for ref in refs if (sub := self.fetch_subscription(ref))]

    def signed_event(self, event_type: str, ref: str) -> tuple[dict[str, str], bytes]:
        body = json.dumps(
            {"id": f"evt_{secrets.token_hex(8)}", "type": event_type, "subscription": ref}
        ).encode()
        return {SIGNATURE_HEADER: sign(self.settings.payment_webhook_secret, body)}, body


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _date(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None

"""The payment provider interface (brief, section 10).

The real provider (Paddle, Lemon Squeezy or Stripe) gets an adapter that implements
`PaymentProvider`; nothing else in the API depends on which one it is.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.models import User

PlanName = Literal["pro_monthly", "pro_yearly", "lifetime"]
Status = Literal["active", "past_due", "canceled", "expired", "refunded"]


class WebhookRejectedError(Exception):
    """The webhook's signature or body is invalid. Retrying won't help (HTTP 400)."""


class WebhookRetryError(Exception):
    """Processing failed for now; the provider should deliver the event again (HTTP 503)."""


@dataclass(frozen=True)
class Checkout:
    url: str


@dataclass(frozen=True)
class ProviderEvent:
    id: str
    type: str
    subscription_ref: str


@dataclass(frozen=True)
class ProviderSubscription:
    """The provider's current view of one subscription or Lifetime purchase."""

    ref: str
    user_id: uuid.UUID
    plan: PlanName
    status: Status
    current_period_end: datetime | None
    past_due_since: datetime | None = None


class PaymentProvider(Protocol):
    name: str

    def create_checkout(self, user: User, plan: PlanName) -> Checkout: ...

    def portal_url(self, user: User) -> str: ...

    def verify_webhook(self, headers: dict[str, str], body: bytes) -> None:
        """Raise WebhookRejectedError unless the request really came from the provider."""

    def parse_event(self, payload: bytes) -> ProviderEvent: ...

    def fetch_subscription(self, ref: str) -> ProviderSubscription | None: ...

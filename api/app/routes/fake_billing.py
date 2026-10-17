"""Development-only checkout and portal pages for FakeProvider.

They act like a hosted provider: change the subscription, then deliver a signed webhook to
our own handler. Never registered in production.
"""

import html
import secrets
import uuid
from dataclasses import replace
from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.billing.fake import FakeProvider
from app.billing.provider import ProviderSubscription
from app.billing.service import handle_webhook
from app.clock import utcnow
from app.config import Settings, get_settings
from app.db import DbSession
from app.errors import AppError
from app.redis_client import RedisClient
from app.security.sessions import RequiredAuth

router = APIRouter(prefix="/billing/fake", include_in_schema=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]
PERIODS = {"pro_monthly": timedelta(days=30), "pro_yearly": timedelta(days=365)}

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fake payments (development)</title>
<style>body{{font:16px system-ui;max-width:40rem;margin:3rem auto;padding:0 1rem;
color:#1e1b4b;background:#fafaf7}}button{{font:inherit;padding:.4rem .8rem;margin:.2rem}}
.note{{background:#fff3cd;padding:.6rem;border-radius:.4rem}}li{{margin:.8rem 0}}</style>
</head><body><p class="note">Fake payment provider for local development. No money moves.</p>
{body}</body></html>"""


def page(body: str) -> HTMLResponse:
    return HTMLResponse(PAGE.format(body=body))


def provider(settings: SettingsDep, redis: RedisClient) -> FakeProvider:
    return FakeProvider(settings, redis)


Fake = Annotated[FakeProvider, Depends(provider)]


def deliver(db: DbSession, fake: FakeProvider, event_type: str, ref: str) -> None:
    headers, body = fake.signed_event(event_type, ref)
    handle_webhook(db, fake, headers, body)


@router.get("/checkout/{session}", response_class=HTMLResponse)
def checkout_page(session: str, fake: Fake) -> HTMLResponse:
    pending = fake.pending_checkout(session)
    if pending is None:
        return page("<h1>Checkout expired</h1><p>Start again from the pricing page.</p>")
    plan = html.escape(pending["plan"])
    return page(
        f"<h1>Buy {plan}</h1>"
        f'<form method="post" action="/billing/fake/checkout/{session}/complete">'
        '<button type="submit">Pay (test)</button></form>'
        f'<form method="post" action="/billing/fake/checkout/{session}/cancel">'
        '<button type="submit">Cancel</button></form>'
    )


@router.post("/checkout/{session}/complete")
def complete_checkout(
    session: str, db: DbSession, fake: Fake, settings: SettingsDep
) -> RedirectResponse:
    pending = fake.pending_checkout(session)
    if pending is None:
        return RedirectResponse(f"{settings.web_origin}/pricing?checkout=expired", 303)
    plan = pending["plan"]
    sub = ProviderSubscription(
        ref=f"sub_{secrets.token_hex(8)}",
        user_id=uuid.UUID(pending["user_id"]),
        plan=plan,
        status="active",
        current_period_end=None if plan == "lifetime" else utcnow() + PERIODS[plan],
    )
    fake.save(sub)
    fake.close_checkout(session)
    deliver(db, fake, "checkout.completed", sub.ref)
    return RedirectResponse(f"{settings.web_origin}/account?checkout=success", 303)


@router.post("/checkout/{session}/cancel")
def cancel_checkout(session: str, fake: Fake, settings: SettingsDep) -> RedirectResponse:
    fake.close_checkout(session)
    return RedirectResponse(f"{settings.web_origin}/pricing?checkout=canceled", 303)


ACTIONS = {
    "renew": "Renewal paid",
    "fail": "Payment failed",
    "cancel": "Cancel",
    "resume": "Resume",
    "end": "End now",
    "refund": "Refund",
}


@router.get("/portal", response_class=HTMLResponse)
def portal_page(auth: RequiredAuth, fake: Fake, settings: SettingsDep) -> HTMLResponse:
    items = []
    for sub in fake.subscriptions_for(auth.user.id):
        buttons = "".join(
            f'<form method="post" action="/billing/fake/portal/{sub.ref}" style="display:inline">'
            f'<input type="hidden" name="action" value="{key}"><button>{label}</button></form>'
            for key, label in ACTIONS.items()
            if sub.plan != "lifetime" or key == "refund"
        )
        end = sub.current_period_end.date().isoformat() if sub.current_period_end else "never"
        items.append(
            f"<li><strong>{html.escape(sub.plan)}</strong> · {html.escape(sub.status)} · "
            f"period ends {end}<br>{buttons}</li>"
        )
    body = "".join(items) or "<li>No subscriptions.</li>"
    return page(
        f"<h1>Billing portal</h1><ul>{body}</ul>"
        f'<p><a href="{html.escape(settings.web_origin)}/account">Back to zagoat</a></p>'
    )


@router.post("/portal/{ref}")
def portal_action(
    ref: str,
    action: Annotated[str, Form()],
    db: DbSession,
    auth: RequiredAuth,
    fake: Fake,
) -> RedirectResponse:
    sub = fake.fetch_subscription(ref)
    if sub is None or sub.user_id != auth.user.id or action not in ACTIONS:
        raise AppError(status.HTTP_404_NOT_FOUND, "not_found", "We couldn't find that.")
    now = utcnow()
    period = PERIODS.get(sub.plan, timedelta(0))
    table: dict[str, dict[str, Any]] = {
        "renew": {
            "status": "active",
            "current_period_end": max(sub.current_period_end or now, now) + period,
            "past_due_since": None,
        },
        "fail": {"status": "past_due", "past_due_since": now},
        "cancel": {"status": "canceled"},
        "resume": {"status": "active", "past_due_since": None},
        "end": {"status": "expired", "current_period_end": now},
        "refund": {"status": "refunded"},
    }
    fake.save(replace(sub, **table[action]))
    deliver(db, fake, f"subscription.{action}", ref)
    return RedirectResponse("/billing/fake/portal", 303)

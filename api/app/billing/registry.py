from typing import Annotated

from fastapi import Depends, status

from app.billing.fake import FakeProvider
from app.billing.provider import PaymentProvider
from app.config import Settings, get_settings
from app.errors import AppError
from app.redis_client import RedisClient


def get_provider(
    settings: Annotated[Settings, Depends(get_settings)], redis: RedisClient
) -> PaymentProvider:
    if settings.payment_provider == "fake":
        return FakeProvider(settings, redis)
    raise AppError(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "payments_unavailable",
        "Payments aren't available yet. Join the waitlist to hear when they open.",
    )


Provider = Annotated[PaymentProvider, Depends(get_provider)]

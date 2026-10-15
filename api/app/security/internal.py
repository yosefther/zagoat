"""Protection for /internal routes: shared secret plus IP allowlist (section 13)."""

import hmac
import ipaddress
from typing import Annotated

from fastapi import Depends, Request, status

from app.config import Settings, get_settings
from app.errors import AppError
from app.ratelimit import client_ip


def ip_allowed(ip: str, allowed: tuple[str, ...]) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(address in ipaddress.ip_network(entry, strict=False) for entry in allowed)


def require_worker(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> None:
    secret = request.headers.get("X-Worker-Secret", "")
    if not ip_allowed(client_ip(request), settings.worker_allowed_ips) or not hmac.compare_digest(
        secret.encode(), settings.worker_secret.encode()
    ):
        # Same answer for both failures, so probing reveals nothing.
        raise AppError(status.HTTP_404_NOT_FOUND, "not_found", "We couldn't find that.")

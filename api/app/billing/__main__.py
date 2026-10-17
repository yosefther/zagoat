"""Billing jobs.

uv run python -m app.billing reconcile   compare paid users with the provider (nightly)
"""

import argparse
import sys

from app.billing.fake import FakeProvider
from app.billing.service import reconcile
from app.config import get_settings
from app.db import get_sessionmaker
from app.redis_client import get_redis


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.billing")
    parser.add_argument("command", choices=["reconcile"])
    parser.parse_args(argv)
    settings = get_settings()
    if settings.payment_provider != "fake":
        print("No payment provider is configured; nothing to reconcile.")
        return 0
    provider = FakeProvider(settings, get_redis(settings))
    with get_sessionmaker(settings)() as db:
        report = reconcile(db, provider, settings)
    print(f"checked {report.checked}")
    print(f"fixed: {', '.join(report.fixed) or '-'}")
    print(f"expired: {', '.join(report.expired) or '-'}")
    print(f"missing at provider: {', '.join(report.missing) or '-'}")
    return 1 if report.missing else 0


if __name__ == "__main__":
    sys.exit(main())

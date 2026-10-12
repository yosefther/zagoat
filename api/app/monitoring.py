import sentry_sdk

from app.config import Settings


def init_sentry(settings: Settings) -> None:
    """Start Sentry when a DSN is configured; otherwise do nothing."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment.value,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )

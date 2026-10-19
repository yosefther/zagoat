"""API configuration.

Every tunable value for the API (limits, prices, caps, timeouts) lives here and is read
from the environment. Defaults are set for local development against
infra/docker-compose.yml; production must set every required value explicitly.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


# Settings that have a local-dev default but must be set explicitly in production.
REQUIRED_IN_PRODUCTION = (
    "database_url",
    "redis_url",
    "web_origin",
    "api_origin",
    "secret_key",
    "worker_secret",
    "worker_allowed_ips",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    environment: Environment = Environment.DEVELOPMENT

    database_url: str = "postgresql+psycopg://zagoat:zagoat@localhost:5432/zagoat"
    redis_url: str = "redis://localhost:6379/0"

    # The only origin allowed by CORS (section 13).
    web_origin: str = "http://localhost:3000"

    # Signs CSRF tokens. Production must set a long random value.
    secret_key: str = "dev-only-secret-change-me"  # noqa: S105

    # Cookies. Set COOKIE_DOMAIN to the shared parent domain (e.g. "zagoat.io") in production
    # so the web app at zagoat.io and the API at api.zagoat.io share them.
    cookie_domain: str | None = None
    cookie_secure: bool = False
    csrf_cookie_name: str = "zagoat_csrf"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_cookie_max_age_seconds: int = 60 * 60 * 24 * 30

    # Database connection pool.
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_connect_timeout_seconds: int = 5

    # How long /healthz waits on each dependency before reporting it down.
    healthcheck_timeout_seconds: float = 2.0

    # Public URL of this API; OAuth providers redirect back to it.
    api_origin: str = "http://localhost:8000"

    # Sessions (section 3: server-side sessions in HTTP-only cookies).
    session_cookie_name: str = "zagoat_session"
    session_lifetime_days: int = 30

    # OAuth sign-in. A provider is offered only when both its id and secret are set.
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    oauth_state_ttl_seconds: int = 600
    oauth_http_timeout_seconds: float = 10.0

    # Local-only sign-in without OAuth, for development. Refused in production.
    dev_login_enabled: bool = False

    # Largest draft or submission, all files together (section 9, proposed).
    max_code_bytes: int = 1_000_000

    # Job queue shared with the runner (JSON messages on a Redis list).
    queue_key: str = "zagoat:jobs"
    # Jobs older than this never ran: the worker drops them, and the API gives up on them a
    # little later in case the worker is down (section 9).
    queue_timeout_seconds: int = 300
    queue_timeout_grace_seconds: int = 60
    # Longest a job may run before the API treats it as lost (Submit limit plus slack).
    job_run_timeout_seconds: int = 300

    # Internal routes for the runner: shared secret plus IP allowlist (section 13).
    worker_secret: str = "dev-only-worker-secret"  # noqa: S105
    worker_allowed_ips: tuple[str, ...] = ("127.0.0.1", "::1")

    # Plans and limits (sections 8 and 9). Lifetime and Pro share the paid limits.
    free_submits_per_day: int = 10
    paid_submits_per_day: int = 100  # fair use, proposed
    free_runs_per_hour: int = 30  # proposed
    paid_runs_per_hour: int = 120  # proposed
    # A Pro subscription whose payment failed keeps access this long (section 10, proposed).
    past_due_grace_days: int = 7

    # Billing (section 10). The provider isn't chosen yet; "fake" works locally and in tests.
    # With no provider, billing routes answer "not available yet".
    payment_provider: Literal["fake"] | None = "fake"
    payment_webhook_secret: str = "dev-only-webhook-secret"  # noqa: S105
    currency: str = "USD"
    # Lifetime: unset price means it isn't on sale. Only the first `lifetime_cap` are offered.
    lifetime_price_cents: int | None = None
    lifetime_cap: int = 100
    # Pro stays off until the library reaches about 20 problems (section 8).
    pro_subscriptions_enabled: bool = False
    pro_monthly_price_cents: int = 1500
    pro_yearly_price_cents: int = 9900

    # Sign-in and waitlist attempts per IP (section 9, proposed).
    ip_attempts_per_hour: int = 5

    # Monitoring. Sentry stays off until a DSN is set.
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0

    @model_validator(mode="after")
    def _require_explicit_production_values(self) -> Self:
        if self.environment is Environment.PRODUCTION:
            missing = [name for name in REQUIRED_IN_PRODUCTION if name not in self.model_fields_set]
            if missing:
                names = ", ".join(name.upper() for name in missing)
                raise ValueError(f"Production requires these settings to be set: {names}")
            if not self.cookie_secure:
                raise ValueError("Production requires COOKIE_SECURE=true")
            if self.dev_login_enabled:
                raise ValueError("DEV_LOGIN_ENABLED must be false in production")
            if self.payment_provider == "fake":
                raise ValueError("PAYMENT_PROVIDER=fake is for development; leave it empty")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()

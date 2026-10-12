"""API configuration.

Every tunable value for the API (limits, prices, caps, timeouts) lives here and is read
from the environment. Defaults are set for local development against
infra/docker-compose.yml; production must set every required value explicitly.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


# Settings that have a local-dev default but must be set explicitly in production.
REQUIRED_IN_PRODUCTION = ("database_url", "redis_url", "web_origin", "secret_key")


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
        return self

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()

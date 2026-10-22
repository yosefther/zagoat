from typing import Any

import pytest
from pydantic import ValidationError

from app.config import Environment, Settings

PRODUCTION: dict[str, Any] = {
    "environment": Environment.PRODUCTION,
    "database_url": "postgresql+psycopg://u:p@db:5432/zagoat",
    "redis_url": "redis://cache:6379/0",
    "web_origin": "https://zagoat.io",
    "api_origin": "https://api.zagoat.io",
    "secret_key": "k" * 40,
    "cookie_secure": True,
    "worker_secret": "w" * 40,
    "worker_allowed_ips": ("198.51.100.7",),
    "payment_provider": None,
}


def production(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **{**PRODUCTION, **overrides})


def test_development_works_with_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.web_origin == "http://localhost:3000"


def test_production_refuses_to_start_on_defaults() -> None:
    expected = "DATABASE_URL, REDIS_URL, WEB_ORIGIN, API_ORIGIN, SECRET_KEY, WORKER_SECRET"
    with pytest.raises(ValidationError, match=expected):
        Settings(_env_file=None, environment=Environment.PRODUCTION, cookie_secure=True)


def test_production_accepts_explicit_values() -> None:
    assert production().is_production


@pytest.mark.parametrize(
    "overrides",
    [
        {"secret_key": "dev-only-secret-change-me"},
        {"worker_secret": "dev-only-worker-secret"},
        {"secret_key": "short-secret"},
    ],
)
def test_production_refuses_example_or_short_secrets(overrides: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="random secrets"):
        production(**overrides)


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        production(cookie_secure=False)


def test_production_refuses_the_fake_payment_provider() -> None:
    with pytest.raises(ValidationError, match="PAYMENT_PROVIDER=fake"):
        production(payment_provider="fake")


def test_production_refuses_dev_login() -> None:
    with pytest.raises(ValidationError, match="DEV_LOGIN_ENABLED"):
        production(dev_login_enabled=True)


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_ORIGIN", "https://example.test")
    monkeypatch.setenv("HEALTHCHECK_TIMEOUT_SECONDS", "0.25")

    settings = Settings(_env_file=None)

    assert settings.web_origin == "https://example.test"
    assert settings.healthcheck_timeout_seconds == 0.25

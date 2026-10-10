import pytest
from pydantic import ValidationError

from app.config import Environment, Settings


def test_development_works_with_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.web_origin == "http://localhost:3000"


def test_production_refuses_to_start_on_defaults() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL, REDIS_URL, WEB_ORIGIN, SECRET_KEY"):
        Settings(_env_file=None, environment=Environment.PRODUCTION)


def test_production_accepts_explicit_values() -> None:
    settings = Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        database_url="postgresql+psycopg://u:p@db:5432/zagoat",
        redis_url="redis://cache:6379/0",
        web_origin="https://zagoat.io",
        secret_key="a-long-random-secret",
        cookie_secure=True,
    )

    assert settings.is_production


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(
            _env_file=None,
            environment=Environment.PRODUCTION,
            database_url="postgresql+psycopg://u:p@db:5432/zagoat",
            redis_url="redis://cache:6379/0",
            web_origin="https://zagoat.io",
            secret_key="a-long-random-secret",
        )


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_ORIGIN", "https://example.test")
    monkeypatch.setenv("HEALTHCHECK_TIMEOUT_SECONDS", "0.25")

    settings = Settings(_env_file=None)

    assert settings.web_origin == "https://example.test"
    assert settings.healthcheck_timeout_seconds == 0.25

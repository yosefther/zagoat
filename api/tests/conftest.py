import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Environment, Settings
from app.main import create_app

# Tests use their own database and Redis db number so they never touch dev data.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://zagoat:zagoat@localhost:5432/zagoat_test"
)
TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment=Environment.TEST,
        database_url=TEST_DATABASE_URL,
        redis_url=TEST_REDIS_URL,
        web_origin="http://localhost:3000",
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client

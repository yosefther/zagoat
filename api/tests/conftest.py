import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.config import Environment, Settings
from app.db import get_db
from app.main import create_app
from app.models import User

# Tests use their own database and Redis db number so they never touch dev data.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://zagoat:zagoat@localhost:5432/zagoat_test"
)
TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
WEB_ORIGIN = "http://localhost:3000"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.TEST,
        "database_url": TEST_DATABASE_URL,
        "redis_url": TEST_REDIS_URL,
        "web_origin": WEB_ORIGIN,
        "secret_key": "test-secret",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """A freshly migrated test database, shared by the whole run."""
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
        config = Config(ALEMBIC_INI)
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session whose work is rolled back after each test, even if the code commits."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def redis() -> Iterator[Redis]:
    client = Redis.from_url(TEST_REDIS_URL)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def app(settings: Settings, db: Session, redis: Redis) -> FastAPI:
    app = create_app(settings)
    app.dependency_overrides[get_db] = lambda: db
    return app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client


def csrf_headers(client: TestClient) -> dict[str, str]:
    """Fetch a CSRF token the way the web app does and return the header to send."""
    token = client.get("/csrf").json()["csrf_token"]
    return {"X-CSRF-Token": token}


def sign_in(client: TestClient, db: Session, email: str = "ada@example.com") -> User:
    """Create a user with a live session and put the session cookie on the client."""
    from app.security.sessions import create_session

    user = User(email=email, name="Ada")
    db.add(user)
    db.flush()
    token, _ = create_session(db, make_settings(), user)
    db.commit()
    client.cookies.set("zagoat_session", token)
    return user

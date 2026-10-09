from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_healthz_reports_ok_when_dependencies_are_up(client: TestClient) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


def test_healthz_returns_503_when_redis_is_down(settings: Settings) -> None:
    broken = settings.model_copy(
        update={"redis_url": "redis://localhost:1/0", "healthcheck_timeout_seconds": 0.5}
    )
    client = TestClient(create_app(broken))

    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json() == {"status": "down", "checks": {"database": "ok", "redis": "down"}}


def test_healthz_returns_503_when_database_is_down(settings: Settings) -> None:
    broken = settings.model_copy(
        update={
            "database_url": "postgresql+psycopg://zagoat:zagoat@localhost:1/zagoat",
            "db_connect_timeout_seconds": 1,
        }
    )
    client = TestClient(create_app(broken))

    response = client.get("/healthz")

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "down"

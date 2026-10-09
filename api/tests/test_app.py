from fastapi.testclient import TestClient

from app.config import Environment, Settings
from app.main import create_app


def test_cors_allows_the_web_origin(client: TestClient) -> None:
    response = client.options(
        "/healthz",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_rejects_other_origins(client: TestClient) -> None:
    response = client.get("/healthz", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers


def test_docs_are_served_outside_production(client: TestClient) -> None:
    assert client.get("/openapi.json").status_code == 200


def test_docs_are_hidden_in_production(settings: Settings) -> None:
    production = Settings(
        _env_file=None,
        environment=Environment.PRODUCTION,
        database_url=settings.database_url,
        redis_url=settings.redis_url,
        web_origin="https://zagoat.io",
    )
    client = TestClient(create_app(production))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404

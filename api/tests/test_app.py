from fastapi.testclient import TestClient

from app.config import Environment, Settings
from app.main import create_app
from tests.conftest import make_settings


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
    production = make_settings(
        environment=Environment.PRODUCTION,
        web_origin="https://zagoat.io",
        api_origin="https://api.zagoat.io",
        cookie_secure=True,
        secret_key="k" * 40,
        worker_secret="w" * 40,
        worker_allowed_ips=("198.51.100.7",),
        payment_provider=None,
    )
    client = TestClient(create_app(production))

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404

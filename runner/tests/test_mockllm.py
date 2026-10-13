import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mockllm.app import FALLBACK_REPLY, create_app
from mockllm.embeddings import hashed_embedding

KEY = {"Authorization": "Bearer zagoat-demo-01-abc123"}
OTHER_JOB = {"Authorization": "Bearer zagoat-demo-01-def456"}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    task = tmp_path / "demo-01"
    (task / "fixtures").mkdir(parents=True)
    (task / "problem.yaml").write_text("id: demo-01\nmock_llm: fixtures/llm.jsonl\n")
    rows = [
        {"kind": "chat", "user": "What is  2+2?", "response": "4"},
        {"kind": "embedding", "input": "fixed text", "vector": [1.0, 0.0]},
    ]
    (task / "fixtures" / "llm.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    return TestClient(create_app(tmp_path))


def chat(client: TestClient, text: str, headers: dict[str, str] = KEY) -> str:
    response = client.post(
        "/v1/chat/completions",
        json={"model": "m", "messages": [{"role": "user", "content": text}]},
        headers=headers,
    )
    assert response.status_code == 200
    return str(response.json()["choices"][0]["message"]["content"])


def test_matching_prompt_gets_recorded_answer(client: TestClient) -> None:
    assert chat(client, "What is 2+2?\n") == "4"


def test_unknown_prompt_gets_fallback(client: TestClient) -> None:
    assert chat(client, "Something else") == FALLBACK_REPLY


def test_embeddings_use_fixture_vectors_then_hashing(client: TestClient) -> None:
    response = client.post(
        "/v1/embeddings", json={"model": "e", "input": ["fixed text", "new text"]}, headers=KEY
    )

    data = response.json()["data"]
    assert data[0]["embedding"] == [1.0, 0.0]
    assert data[1]["embedding"] == hashed_embedding("new text", 256)


def test_hashed_embeddings_are_deterministic_and_lexical() -> None:
    a = hashed_embedding("refund timing for card payments", 256)
    b = hashed_embedding("how long does a card refund take", 256)
    c = hashed_embedding("tent poles and guy lines", 256)

    def dot(x: list[float], y: list[float]) -> float:
        return sum(i * j for i, j in zip(x, y, strict=True))

    assert a == hashed_embedding("refund timing for card payments", 256)
    assert dot(a, b) > dot(a, c)


def test_calls_are_logged_per_job(client: TestClient) -> None:
    chat(client, "What is 2+2?")
    chat(client, "hello", headers=OTHER_JOB)

    calls = client.get("/_calls", headers=KEY).json()["calls"]

    assert len(calls) == 1
    assert calls[0]["request"]["messages"][0]["content"] == "What is 2+2?"
    client.delete("/_calls", headers=KEY)
    assert client.get("/_calls", headers=KEY).json()["calls"] == []


@pytest.mark.parametrize("auth", [None, "Bearer sk-real-key", "Basic abc"])
def test_requests_need_a_job_key(client: TestClient, auth: str | None) -> None:
    headers = {"Authorization": auth} if auth else {}

    assert client.post("/v1/chat/completions", json={}, headers=headers).status_code == 401


def test_streaming_is_refused(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions", json={"messages": [], "stream": True}, headers=KEY
    )

    assert response.status_code == 400

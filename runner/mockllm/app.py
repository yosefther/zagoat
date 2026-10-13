"""OpenAI-compatible mock LLM (brief, section 5).

Sandboxes reach it at OPENAI_BASE_URL with OPENAI_API_KEY set to a per-job key of the form
`zagoat-<problem id>-<nonce>`. The key picks the task's fixtures and keys the call log that
graders read through GET /_calls.
"""

import time
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from mockllm.embeddings import hashed_embedding
from mockllm.fixtures import TaskFixtures, load_all_fixtures, normalize

FALLBACK_REPLY = "I can't answer that from the information I was given."


class Limits(BaseModel):
    embedding_dim: int = 256
    max_jobs_logged: int = 500
    max_calls_per_job: int = 1000
    max_inputs_per_request: int = 2048


def _job_key(authorization: str | None) -> tuple[str, str]:
    """Return (key, problem_id) from 'Bearer zagoat-<problem>-<nonce>'."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing API key")
    key = authorization.removeprefix("Bearer ").strip()
    if not key.startswith("zagoat-") or key.count("-") < 2:
        raise HTTPException(401, "Invalid API key")
    problem_id = key.removeprefix("zagoat-").rsplit("-", 1)[0]
    return key, problem_id


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, list):  # content parts: keep the text ones
                return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
            return str(content or "")
    return ""


def create_app(problems_dir: Path, limits: Limits | None = None) -> FastAPI:
    limits = limits or Limits()
    fixtures: dict[str, TaskFixtures] = load_all_fixtures(problems_dir)
    calls: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
    app = FastAPI(title="zagoat mock LLM", docs_url=None, redoc_url=None, openapi_url=None)

    def log(key: str, endpoint: str, request: dict[str, Any], response: Any) -> None:
        job_calls = calls.setdefault(key, [])
        calls.move_to_end(key)
        while len(calls) > limits.max_jobs_logged:
            calls.popitem(last=False)
        if len(job_calls) < limits.max_calls_per_job:
            job_calls.append({"endpoint": endpoint, "request": request, "response": response})

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/chat/completions")
    async def chat(
        request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        key, problem_id = _job_key(authorization)
        body = await request.json()
        if body.get("stream"):
            raise HTTPException(400, "Streaming is not supported by the mock LLM")
        prompt = normalize(_last_user_message(body.get("messages", [])))
        task = fixtures.get(problem_id, TaskFixtures())
        reply = task.chat.get(prompt, FALLBACK_REPLY)
        log(key, "chat.completions", body, reply)
        prompt_tokens = len(prompt.split())
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", "mock"),
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": len(reply.split()),
                "total_tokens": prompt_tokens + len(reply.split()),
            },
        }

    @app.post("/v1/embeddings")
    async def embeddings(
        request: Request, authorization: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        key, problem_id = _job_key(authorization)
        body = await request.json()
        raw = body.get("input", [])
        inputs = [raw] if isinstance(raw, str) else list(raw)
        if not inputs or not all(isinstance(text, str) for text in inputs):
            raise HTTPException(400, "input must be a string or a list of strings")
        if len(inputs) > limits.max_inputs_per_request:
            raise HTTPException(400, f"At most {limits.max_inputs_per_request} inputs per request")
        task = fixtures.get(problem_id, TaskFixtures())
        vectors = [
            task.embeddings.get(normalize(text)) or hashed_embedding(text, limits.embedding_dim)
            for text in inputs
        ]
        log(key, "embeddings", {"model": body.get("model"), "input": inputs}, len(vectors))
        return {
            "object": "list",
            "model": body.get("model", "mock-embedding"),
            "data": [
                {"object": "embedding", "index": i, "embedding": vector}
                for i, vector in enumerate(vectors)
            ],
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }

    @app.get("/_calls")
    def list_calls(authorization: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        key, _ = _job_key(authorization)
        return {"calls": calls.get(key, [])}

    @app.delete("/_calls", status_code=204)
    def clear_calls(authorization: Annotated[str | None, Header()] = None) -> None:
        key, _ = _job_key(authorization)
        calls.pop(key, None)

    return app

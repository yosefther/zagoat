import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx2
import pytest
from redis import Redis

from zagoat_runner.config import Settings
from zagoat_runner.executor import Job, write_files
from zagoat_runner.grading import ExecResult, Outcome
from zagoat_runner.taskspec import load_task
from zagoat_runner.worker import ApiClient, Worker

REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
JOB_ID = "a" * 32


@dataclass
class FakeExecutor:
    result: ExecResult
    jobs: list[Job] = field(default_factory=list)

    def execute(self, job: Job, time_limit_seconds: int) -> ExecResult:
        self.jobs.append(job)
        return self.result


@dataclass
class FakeApi:
    events: list[tuple[str, str, Any]] = field(default_factory=list)

    def started(self, job_id: str) -> bool:
        self.events.append(("started", job_id, None))
        return True

    def result(self, job_id: str, outcome: Outcome, duration_ms: int) -> bool:
        self.events.append(("result", job_id, outcome))
        return True


@pytest.fixture
def redis() -> Redis:
    client = Redis.from_url(REDIS_URL)
    client.flushdb()
    return client


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    root = tmp_path / "tiny-01"
    write_files(
        root,
        {
            "problem.yaml": "id: tiny-01\nimage: zagoat-py312-ml\n",
            "starter/main.py": "x = 1\n",
            "reference/main.py": "x = 2\n",
            "tests/sample/test_s.py": "def test_s():\n    pass\n",
            "tests/hidden/test_h.py": "def test_h():\n    pass\n",
        },
    )
    return Settings(_env_file=None, problems_dir=tmp_path, worker_llm_url="http://127.0.0.1:9")


def make_worker(settings: Settings, redis: Redis, executor: FakeExecutor) -> tuple[Worker, FakeApi]:
    api = FakeApi()
    task = load_task(settings.problems_dir / "tiny-01")
    worker = Worker(settings, redis, executor, api, {"tiny-01": task})  # type: ignore[arg-type]
    return worker, api


def message(**overrides: Any) -> str:
    body = {
        "job_id": JOB_ID,
        "problem_id": "tiny-01",
        "problem_version": 1,
        "kind": "submit",
        "files": {"main.py": "x = 2\n"},
        "enqueued_at": time.time(),
    }
    body.update(overrides)
    return json.dumps(body)


PASSED = ExecResult(
    exit_code=0,
    duration_ms=50,
    results={
        "tests": [{"name": "h", "outcome": "passed", "message": None}],
        "metrics": {},
        "collection_errors": [],
    },
)


def test_job_runs_and_reports(settings: Settings, redis: Redis) -> None:
    executor = FakeExecutor(PASSED)
    worker, api = make_worker(settings, redis, executor)

    worker.handle(message())

    assert [e[0] for e in api.events] == ["started", "result"]
    assert api.events[1][2].verdict == "passed"
    job = executor.jobs[0]
    assert job.kind == "submit"
    assert job.llm_key == f"zagoat-tiny-01-{JOB_ID}"


def test_old_jobs_are_dropped_as_system_error(settings: Settings, redis: Redis) -> None:
    executor = FakeExecutor(PASSED)
    worker, api = make_worker(settings, redis, executor)

    worker.handle(message(enqueued_at=time.time() - 301))

    assert executor.jobs == []
    assert [e[0] for e in api.events] == ["result"]
    assert api.events[0][2].verdict == "system_error"


def test_unknown_problem_is_a_system_error(settings: Settings, redis: Redis) -> None:
    worker, api = make_worker(settings, redis, FakeExecutor(PASSED))

    worker.handle(message(problem_id="missing-01"))

    assert api.events[0][2].verdict == "system_error"


def test_malformed_messages_are_dropped(settings: Settings, redis: Redis) -> None:
    worker, api = make_worker(settings, redis, FakeExecutor(PASSED))

    worker.handle("not json")
    worker.handle(message(job_id="../../etc"))

    assert api.events == []


def test_recover_requeues_unfinished_jobs(settings: Settings, redis: Redis) -> None:
    worker, _ = make_worker(settings, redis, FakeExecutor(PASSED))
    redis.lpush(worker.processing_key(0), message())

    worker.recover()

    assert redis.llen(settings.queue_key) == 1
    assert redis.llen(worker.processing_key(0)) == 0


def test_api_client_retries_server_errors(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        return httpx2.Response(503 if len(calls) < 3 else 204)

    monkeypatch.setattr("zagoat_runner.worker.time.sleep", lambda _: None)
    http = httpx2.Client(base_url="http://api.test", transport=httpx2.MockTransport(handler))

    assert ApiClient(settings, http).started(JOB_ID)
    assert len(calls) == 3
    assert calls[0].headers["X-Worker-Secret"] == settings.worker_secret

import json
import uuid
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from redis import Redis
from sqlalchemy.orm import Session

from app.models import Submission
from tests.conftest import csrf_headers, sign_in
from tests.problem_factory import add_problem

WORKER = {"X-Worker-Secret": "dev-only-worker-secret"}
FIXED = {"main.py": "def add(a, b):\n    return a + b\n"}


@pytest.fixture
def worker(app: FastAPI) -> TestClient:
    return TestClient(app, client=("127.0.0.1", 50000))


def start_job(client: TestClient, kind: str = "runs", problem_id: str = "free-01") -> Response:
    return client.post(
        f"/problems/{problem_id}/{kind}", json={"files": FIXED}, headers=csrf_headers(client)
    )


@pytest.fixture
def user_client(client: TestClient, db: Session) -> TestClient:
    add_problem(db, "free-01")
    sign_in(client, db)
    return client


def test_run_is_queued_as_json(user_client: TestClient, db: Session, redis: Redis) -> None:
    response = start_job(user_client)

    assert response.status_code == 202
    job_id = response.json()["job_id"]
    message = json.loads(redis.rpop("zagoat:jobs"))  # type: ignore[arg-type]
    assert message["job_id"] == job_id
    assert message["kind"] == "run"
    assert message["problem_id"] == "free-01"
    assert message["files"] == {"main.py": FIXED["main.py"], "util.py": "X = 1\n"}
    row = db.get(Submission, uuid.UUID(hex=job_id))
    assert row is not None and row.status == "queued" and row.problem_version == 1


def test_job_status_is_visible_to_its_owner_only(user_client: TestClient, db: Session) -> None:
    job_id = start_job(user_client).json()["job_id"]

    body = user_client.get(f"/jobs/{job_id}").json()
    assert body["status"] == "queued"
    assert body["kind"] == "run"

    other = TestClient(user_client.app)
    sign_in(other, db, email="other@example.com")
    assert other.get(f"/jobs/{job_id}").status_code == 404


def test_one_job_at_a_time(user_client: TestClient) -> None:
    assert start_job(user_client).status_code == 202

    response = start_job(user_client, "submissions")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "job_in_progress"


def test_stale_job_does_not_block_new_ones(user_client: TestClient, db: Session) -> None:
    job_id = start_job(user_client).json()["job_id"]
    row = db.get(Submission, uuid.UUID(hex=job_id))
    assert row is not None
    row.created_at -= timedelta(minutes=10)
    db.commit()

    assert start_job(user_client).status_code == 202
    assert row.verdict == "system_error"


def test_job_stuck_in_queue_becomes_system_error(user_client: TestClient, db: Session) -> None:
    job_id = start_job(user_client).json()["job_id"]
    row = db.get(Submission, uuid.UUID(hex=job_id))
    assert row is not None
    row.created_at -= timedelta(minutes=6, seconds=1)
    db.commit()

    body = user_client.get(f"/jobs/{job_id}").json()

    assert body["status"] == "done"
    assert body["verdict"] == "system_error"
    assert "doesn't count" in body["message"]


def test_visitors_and_paid_locks(client: TestClient, db: Session) -> None:
    add_problem(db, "paid-01", access="paid")
    assert start_job(client, problem_id="paid-01").status_code == 401

    sign_in(client, db)
    response = start_job(client, problem_id="paid-01")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "paid_problem"


def test_jobs_need_csrf(user_client: TestClient) -> None:
    response = user_client.post("/problems/free-01/runs", json={"files": FIXED})

    assert response.status_code == 403


def test_worker_reports_start_and_result(
    user_client: TestClient, worker: TestClient, db: Session
) -> None:
    job_id = start_job(user_client).json()["job_id"]

    assert worker.post(f"/internal/jobs/{job_id}/started", headers=WORKER).status_code == 204
    assert user_client.get(f"/jobs/{job_id}").json()["status"] == "running"

    result = {
        "verdict": "failed",
        "message": "1 of 2 tests failed.",
        "tests_passed": 1,
        "tests_total": 2,
        "tests": [{"name": "Adds", "outcome": "failed", "message": "add(2, 3) should be 5"}],
        "metrics": [],
        "stdout": "hello",
        "stderr": "",
        "duration_ms": 1234,
    }
    assert (
        worker.post(f"/internal/jobs/{job_id}/result", json=result, headers=WORKER).status_code
        == 204
    )

    body = user_client.get(f"/jobs/{job_id}").json()
    assert body["status"] == "done"
    assert body["verdict"] == "failed"
    assert body["tests"][0]["message"] == "add(2, 3) should be 5"
    assert body["stdout"] == "hello"
    assert body["duration_ms"] == 1234


def test_submit_results_never_store_output(user_client: TestClient, worker: TestClient) -> None:
    job_id = start_job(user_client, "submissions").json()["job_id"]
    result = {"verdict": "passed", "stdout": "leaked hidden test output", "stderr": "x"}

    worker.post(f"/internal/jobs/{job_id}/result", json=result, headers=WORKER)

    body = user_client.get(f"/jobs/{job_id}").json()
    assert body["stdout"] is None
    assert body["stderr"] is None


def test_results_are_recorded_once(user_client: TestClient, worker: TestClient) -> None:
    job_id = start_job(user_client).json()["job_id"]
    worker.post(f"/internal/jobs/{job_id}/result", json={"verdict": "passed"}, headers=WORKER)

    worker.post(f"/internal/jobs/{job_id}/result", json={"verdict": "failed"}, headers=WORKER)

    assert user_client.get(f"/jobs/{job_id}").json()["verdict"] == "passed"


def test_internal_routes_need_the_secret(user_client: TestClient, worker: TestClient) -> None:
    job_id = start_job(user_client).json()["job_id"]

    response = worker.post(
        f"/internal/jobs/{job_id}/result",
        json={"verdict": "passed"},
        headers={"X-Worker-Secret": "wrong"},
    )

    assert response.status_code == 404


def test_internal_routes_need_an_allowed_ip(app: FastAPI, user_client: TestClient) -> None:
    job_id = start_job(user_client).json()["job_id"]
    outsider = TestClient(app, client=("203.0.113.9", 50000))

    response = outsider.post(
        f"/internal/jobs/{job_id}/result", json={"verdict": "passed"}, headers=WORKER
    )

    assert response.status_code == 404

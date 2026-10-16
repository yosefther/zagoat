"""Section 9 limits and counters."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Submission, UsageDaily, User
from tests.conftest import (
    finish_job,
    give_subscription,
    sign_in,
    start_job,
    submit_and_finish,
)
from tests.problem_factory import add_problem

NOW = datetime.now(UTC).replace(hour=15, minute=30, second=0, microsecond=0)
TOMORROW = datetime.combine(NOW.date() + timedelta(days=1), datetime.min.time(), UTC)


@pytest.fixture
def user(client: TestClient, db: Session, freeze: Callable[[datetime], None]) -> User:
    freeze(NOW)
    add_problem(db, "free-01")
    return sign_in(client, db)


def set_used(db: Session, user: User, submits: int, day: date | None = None) -> None:
    db.merge(UsageDaily(user_id=user.id, day=day or NOW.date(), submits=submits))
    db.commit()


def test_free_users_get_ten_submits_a_day(
    client: TestClient, worker: TestClient, db: Session, user: User
) -> None:
    set_used(db, user, 9)
    submit_and_finish(client, worker, "free-01")

    response = start_job(client, "free-01")

    assert response.status_code == 429
    error = response.json()["error"]
    assert error["code"] == "submit_limit"
    assert "all 10 Submits" in error["message"]
    assert "Lifetime and Pro raise the limit" in error["message"]
    assert (
        error["resets_at"]
        == (datetime.combine(NOW.date() + timedelta(days=1), datetime.min.time(), UTC)).isoformat()
    )


def test_paid_users_get_a_hundred(
    client: TestClient, worker: TestClient, db: Session, user: User
) -> None:
    give_subscription(db, user, "lifetime")
    set_used(db, user, 99)
    submit_and_finish(client, worker, "free-01")

    response = start_job(client, "free-01")

    assert response.status_code == 429
    assert "all 100 Submits" in response.json()["error"]["message"]
    assert "raise the limit" not in response.json()["error"]["message"]


def test_submits_reset_at_utc_midnight(
    client: TestClient, db: Session, user: User, freeze: Callable[[datetime], None]
) -> None:
    set_used(db, user, 10)
    assert start_job(client, "free-01").status_code == 429

    freeze(TOMORROW)

    assert start_job(client, "free-01").status_code == 202


def test_a_submit_counts_when_queued(client: TestClient, db: Session, user: User) -> None:
    start_job(client, "free-01")

    assert db.get(UsageDaily, (user.id, NOW.date())).submits == 1  # type: ignore[union-attr]


def test_system_error_refunds_the_submit(
    client: TestClient, worker: TestClient, db: Session, user: User
) -> None:
    job_id = start_job(client, "free-01").json()["job_id"]

    finish_job(worker, job_id, "system_error")

    assert db.get(UsageDaily, (user.id, NOW.date())).submits == 0  # type: ignore[union-attr]
    row = db.scalars(select(Submission)).one()
    assert row.counted is False


def test_lost_jobs_are_refunded_when_they_expire(
    client: TestClient, db: Session, user: User, freeze: Callable[[datetime], None]
) -> None:
    job_id = start_job(client, "free-01").json()["job_id"]

    freeze(NOW + timedelta(minutes=7))
    body = client.get(f"/jobs/{job_id}").json()

    assert body["verdict"] == "system_error"
    assert db.get(UsageDaily, (user.id, NOW.date())).submits == 0  # type: ignore[union-attr]


def test_runs_never_use_submits(
    client: TestClient, worker: TestClient, db: Session, user: User
) -> None:
    for _ in range(3):
        job_id = start_job(client, "free-01", kind="run").json()["job_id"]
        finish_job(worker, job_id, "passed")

    assert db.get(UsageDaily, (user.id, NOW.date())) is None
    assert client.get("/me").json()["usage"]["runs_used"] == 3


def test_free_users_get_thirty_runs_an_hour(
    client: TestClient, worker: TestClient, user: User, freeze: Callable[[datetime], None]
) -> None:
    for _ in range(30):
        job_id = start_job(client, "free-01", kind="run").json()["job_id"]
        finish_job(worker, job_id, "passed")

    response = start_job(client, "free-01", kind="run")
    assert response.status_code == 429
    assert "all 30 test runs for this hour" in response.json()["error"]["message"]

    freeze(NOW + timedelta(hours=1))
    assert start_job(client, "free-01", kind="run").status_code == 202


def test_paid_users_get_more_runs(
    client: TestClient, worker: TestClient, db: Session, user: User
) -> None:
    give_subscription(db, user, "lifetime")

    assert client.get("/me").json()["usage"]["runs_limit"] == 120


def test_me_shows_usage_and_reset_times(client: TestClient, db: Session, user: User) -> None:
    set_used(db, user, 4)

    usage = client.get("/me").json()["usage"]

    assert usage["submits_used"] == 4
    assert usage["submits_limit"] == 10
    assert usage["submits_reset_at"].startswith(str(NOW.date() + timedelta(days=1)))
    assert client.get("/problems/free-01").json()["usage"]["submits_used"] == 4

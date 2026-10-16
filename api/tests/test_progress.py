"""Section 11: progress, unlocks, timer, versions, downgrade and deletion."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Draft, Problem, Progress, Submission, Subscription, UsageDaily
from tests.conftest import (
    csrf_headers,
    finish_job,
    give_subscription,
    sign_in,
    start_job,
    submit_and_finish,
)
from tests.problem_factory import add_problem


@pytest.fixture(autouse=True)
def problems(db: Session) -> None:
    add_problem(db, "free-01")
    add_problem(db, "paid-01", access="paid")


def state(client: TestClient, problem_id: str = "free-01") -> str | None:
    progress: str | None = client.get(f"/problems/{problem_id}").json()["progress"]
    return progress


def test_states_move_forward(client: TestClient, worker: TestClient, db: Session) -> None:
    sign_in(client, db)
    assert state(client) is None

    client.put("/problems/free-01/draft", json={"files": {}}, headers=csrf_headers(client))
    assert state(client) == "in_progress"

    submit_and_finish(client, worker, "free-01", "failed")
    assert state(client) == "attempted"

    submit_and_finish(client, worker, "free-01", "passed")
    assert state(client) == "solved"


def test_a_run_starts_progress(client: TestClient, worker: TestClient, db: Session) -> None:
    sign_in(client, db)

    start_job(client, "free-01", kind="run")

    assert state(client) == "in_progress"


def test_solved_is_permanent(client: TestClient, worker: TestClient, db: Session) -> None:
    sign_in(client, db)
    submit_and_finish(client, worker, "free-01", "passed")

    submit_and_finish(client, worker, "free-01", "failed")
    problem = db.get(Problem, "free-01")
    assert problem is not None
    problem.version += 1
    db.commit()

    assert state(client) == "solved"
    assert [p["progress"] for p in client.get("/problems").json() if p["id"] == "free-01"] == [
        "solved"
    ]


def test_system_error_submits_change_nothing(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    sign_in(client, db)

    submit_and_finish(client, worker, "free-01", "system_error")

    body = client.get("/problems/free-01").json()
    assert body["progress"] in (None, "not_started")
    assert body["reference_unlocked"] is False


def test_hints_are_revealed_one_at_a_time(client: TestClient, db: Session) -> None:
    sign_in(client, db)
    headers = csrf_headers(client)

    skip = client.post("/problems/free-01/hints/2", headers=headers)
    assert skip.status_code == 409
    assert skip.json()["error"]["message"] == "Reveal hint 1 first."

    first = client.post("/problems/free-01/hints/1", headers=headers).json()
    assert first == {"number": 1, "hint": "Look at the loop.", "hints_revealed": 1}
    assert client.post("/problems/free-01/hints/1", headers=headers).json()["hints_revealed"] == 1
    client.post("/problems/free-01/hints/2", headers=headers)
    assert client.post("/problems/free-01/hints/3", headers=headers).status_code == 404

    body = client.get("/problems/free-01").json()
    assert body["hints"] == ["Look at the loop.", "Check the bounds."]
    assert body["progress_detail"]["hints_revealed"] == 2


def test_hints_carry_no_penalty(client: TestClient, worker: TestClient, db: Session) -> None:
    sign_in(client, db)
    client.post("/problems/free-01/hints/1", headers=csrf_headers(client))

    submit_and_finish(client, worker, "free-01", "passed")

    assert state(client) == "solved"


def test_timer_is_recorded_but_never_changes_the_verdict(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    sign_in(client, db)
    job_id = start_job(client, "free-01", timer_seconds=1234).json()["job_id"]
    finish_job(worker, job_id, "passed")

    job = client.get(f"/jobs/{job_id}").json()
    assert (job["verdict"], job["timer_seconds"]) == ("passed", 1234)
    assert client.get("/problems/free-01").json()["progress_detail"]["timer_seconds"] == 1234


def test_history_keeps_the_version_each_submit_ran_against(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    sign_in(client, db)
    submit_and_finish(client, worker, "free-01", "failed")
    problem = db.get(Problem, "free-01")
    assert problem is not None
    problem.version = 2
    db.commit()
    submit_and_finish(client, worker, "free-01", "passed")

    history = client.get("/problems/free-01/submissions").json()

    assert [(h["problem_version"], h["verdict"]) for h in history] == [(2, "passed"), (1, "failed")]
    assert len(client.get("/submissions").json()) == 2


def test_downgrade_keeps_work_but_makes_paid_problems_read_only(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    user = sign_in(client, db)
    sub = give_subscription(db, user, "pro_monthly", "active")
    client.put(
        "/problems/paid-01/draft", json={"files": {"main.py": "mine"}}, headers=csrf_headers(client)
    )
    submit_and_finish(client, worker, "paid-01", "passed")

    sub.status = "expired"
    db.commit()

    body = client.get("/problems/paid-01").json()
    assert body["lock"] == "paid"
    assert body["read_only"] is True
    assert body["draft_files"]["main.py"] == "mine"
    assert body["progress"] == "solved"
    assert len(client.get("/problems/paid-01/submissions").json()) == 1
    put = client.put(
        "/problems/paid-01/draft", json={"files": {"main.py": "x"}}, headers=csrf_headers(client)
    )
    assert put.status_code == 403
    assert start_job(client, "paid-01").status_code == 403


def test_untouched_paid_problems_are_not_read_only(client: TestClient, db: Session) -> None:
    sign_in(client, db)

    body = client.get("/problems/paid-01").json()

    assert body["read_only"] is False
    assert body["starter_files"] is None


def test_deleting_the_account_removes_everything(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    user = sign_in(client, db)
    give_subscription(db, user, "lifetime")
    client.put("/problems/free-01/draft", json={"files": {}}, headers=csrf_headers(client))
    submit_and_finish(client, worker, "free-01", "passed")

    client.delete("/me", headers=csrf_headers(client))
    db.expire_all()

    for model in (Draft, Submission, Progress, UsageDaily, Subscription):
        assert db.scalars(select(model)).all() == [], model.__name__

"""The section 8 capability table, through the API."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import (
    csrf_headers,
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


def hint(client: TestClient, problem_id: str, number: int = 1) -> int:
    return client.post(
        f"/problems/{problem_id}/hints/{number}", headers=csrf_headers(client)
    ).status_code


def test_visitors_can_browse_and_read_every_statement(client: TestClient) -> None:
    assert len(client.get("/problems").json()) == 2
    assert client.get("/problems/paid-01").json()["statement"] == "Fix the function."


def test_visitors_must_sign_in_for_everything_else(client: TestClient) -> None:
    assert start_job(client, "free-01").status_code == 401
    assert start_job(client, "free-01", kind="run").status_code == 401
    assert hint(client, "free-01") == 401
    assert client.get("/problems/free-01/walkthrough").status_code == 401
    assert client.get("/problems/free-01/reference").status_code == 401
    assert client.get("/problems/free-01/submissions").status_code == 401


def test_free_users_solve_free_problems(client: TestClient, db: Session) -> None:
    sign_in(client, db)

    assert start_job(client, "free-01", kind="run").status_code == 202


def test_free_users_cannot_solve_paid_problems(client: TestClient, db: Session) -> None:
    sign_in(client, db)

    assert start_job(client, "paid-01").status_code == 403
    assert start_job(client, "paid-01", kind="run").status_code == 403
    assert client.get("/problems/paid-01").json()["lock"] == "paid"


def test_free_users_get_hints_on_free_problems_only(client: TestClient, db: Session) -> None:
    sign_in(client, db)

    assert hint(client, "free-01") == 200
    assert hint(client, "paid-01") == 403


def test_walkthroughs_are_paid_only(client: TestClient, db: Session) -> None:
    user = sign_in(client, db)
    response = client.get("/problems/free-01/walkthrough")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "paid_feature"
    assert client.get("/problems/free-01").json()["walkthrough_unlocked"] is False

    give_subscription(db, user, "lifetime")

    # Paid users can open walkthroughs any time, even before trying the problem.
    assert client.get("/problems/paid-01/walkthrough").json() == {"markdown": "Full solution."}
    assert client.get("/problems/free-01").json()["walkthrough_unlocked"] is True


def test_paid_users_solve_paid_problems(client: TestClient, db: Session) -> None:
    user = sign_in(client, db)
    give_subscription(db, user, "pro_monthly", "active")

    body = client.get("/problems/paid-01").json()

    assert body["lock"] is None
    assert body["plan"] == "pro_monthly"
    assert start_job(client, "paid-01", kind="run").status_code == 202
    assert hint(client, "paid-01") == 200


def test_reference_unlocks_after_first_submit_for_everyone(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    sign_in(client, db)
    assert client.get("/problems/free-01/reference").status_code == 403

    submit_and_finish(client, worker, "free-01", "failed")

    assert client.get("/problems/free-01/reference").json() == {
        "files": {"main.py": "def add(a, b):\n    return a + b\n"}
    }
    assert client.get("/problems/free-01").json()["reference_unlocked"] is True


def test_history_is_available_to_free_users(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    sign_in(client, db)
    submit_and_finish(client, worker, "free-01")

    assert len(client.get("/problems/free-01/submissions").json()) == 1

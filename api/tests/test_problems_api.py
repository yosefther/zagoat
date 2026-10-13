from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import sign_in
from tests.problem_factory import add_problem


def test_list_is_public_and_hides_unpublished(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    hidden = add_problem(db, "draft-01")
    hidden.published = False
    db.commit()

    response = client.get("/problems")

    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == ["free-01"]


def test_visitors_see_statement_but_not_starter(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")

    body = client.get("/problems/free-01").json()

    assert body["statement"] == "Fix the function."
    assert body["hint_count"] == 2
    assert body["lock"] == "sign_in"
    assert body["starter_files"] is None


def test_paid_statements_are_public(client: TestClient, db: Session) -> None:
    add_problem(db, "paid-01", access="paid")

    body = client.get("/problems/paid-01").json()

    assert body["statement"] == "Fix the function."
    assert body["access"] == "paid"


def test_signed_in_free_user_gets_starter_for_free_problem(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    body = client.get("/problems/free-01").json()

    assert body["lock"] is None
    assert set(body["starter_files"]) == {"main.py", "util.py"}


def test_free_user_is_locked_out_of_paid_problem(client: TestClient, db: Session) -> None:
    add_problem(db, "paid-01", access="paid")
    sign_in(client, db)

    body = client.get("/problems/paid-01").json()

    assert body["lock"] == "paid"
    assert body["starter_files"] is None


def test_problem_responses_never_include_solutions(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    text = client.get("/problems/free-01").text + client.get("/problems").text

    assert "return a + b" not in text  # reference solution
    assert "Full solution." not in text  # walkthrough
    assert "Look at the loop." not in text  # hints are revealed one at a time


def test_unknown_problem_is_404(client: TestClient) -> None:
    response = client.get("/problems/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "problem_not_found"

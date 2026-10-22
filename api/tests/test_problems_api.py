from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import finish_job, sign_in, start_job
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


def test_sample_tests_are_public(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")

    body = client.get("/problems/free-01").json()

    assert body["sample_tests"] == {"test_sample.py": "def test_x():\n    pass\n"}


def test_list_shows_best_result_per_problem(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    add_problem(db, "free-01")  # has a "score" metric
    no_metric = add_problem(db, "free-02")
    no_metric.metrics = []
    db.commit()
    sign_in(client, db)
    for value in (0.5, 0.9, 0.7):
        job = start_job(client, "free-01").json()["job_id"]
        finish_job(worker, job, "failed", metrics=[{"name": "score", "value": value}])
    for passed in (3, 1):
        job = start_job(client, "free-02").json()["job_id"]
        finish_job(worker, job, "failed", tests_passed=passed, tests_total=4)
    job = start_job(client, "free-02").json()["job_id"]
    finish_job(worker, job, "system_error", tests_passed=4, tests_total=4)

    best = {p["id"]: p["best_result"] for p in client.get("/problems").json()}

    assert best["free-01"] == {"value": 0.9, "label": "0.90"}
    assert best["free-02"] == {"value": 0.75, "label": "3/4 tests"}


def test_visitors_get_no_best_result(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")

    assert client.get("/problems").json()[0]["best_result"] is None


FEATURED = {
    "order": 1,
    "file": "main.py",
    "code": "def add(a, b):",
    "checks": ["Adds two numbers"],
    "gauge": None,
}


def test_featured_lists_featured_tasks_in_order(client: TestClient, db: Session) -> None:
    second = add_problem(db, "free-02")
    second.featured = {**FEATURED, "order": 2}
    first = add_problem(db, "free-01")
    first.featured = FEATURED
    add_problem(db, "not-featured-01")
    unpublished = add_problem(db, "draft-01")
    unpublished.featured = FEATURED
    unpublished.published = False
    paid = add_problem(db, "paid-01", access="paid")
    paid.featured = FEATURED
    db.commit()

    response = client.get("/problems/featured")

    assert response.status_code == 200
    body = response.json()
    assert [task["id"] for task in body] == ["free-01", "free-02"]
    assert body[0]["code"] == "def add(a, b):"
    assert body[0]["checks"] == ["Adds two numbers"]
    assert "a + b" not in response.text  # never the reference solution

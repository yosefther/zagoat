from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Draft
from tests.conftest import csrf_headers, sign_in
from tests.problem_factory import add_problem

NEW_MAIN = "def add(a, b):\n    return a + b\n"


def save(client: TestClient, problem_id: str, files: dict[str, str]) -> Response:
    return client.put(
        f"/problems/{problem_id}/draft", json={"files": files}, headers=csrf_headers(client)
    )


def test_draft_is_saved_and_returned_with_the_problem(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    response = save(client, "free-01", {"main.py": NEW_MAIN})

    assert response.status_code == 200
    body = client.get("/problems/free-01").json()
    assert body["draft_files"] == {"main.py": NEW_MAIN, "util.py": "X = 1\n"}
    assert body["draft_updated_at"]


def test_saving_again_updates_the_same_draft(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    save(client, "free-01", {"main.py": "v1"})
    save(client, "free-01", {"main.py": "v2"})

    drafts = db.scalars(select(Draft)).all()
    assert len(drafts) == 1
    assert drafts[0].files["main.py"] == "v2"


def test_drafts_are_private(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)
    save(client, "free-01", {"main.py": NEW_MAIN})

    other = TestClient(client.app)
    sign_in(other, db, email="other@example.com")

    assert other.get("/problems/free-01").json()["draft_files"] is None


def test_visitors_cannot_save(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")

    assert save(client, "free-01", {"main.py": NEW_MAIN}).status_code == 401


def test_free_users_cannot_save_paid_drafts(client: TestClient, db: Session) -> None:
    add_problem(db, "paid-01", access="paid")
    sign_in(client, db)

    response = save(client, "paid-01", {"main.py": NEW_MAIN})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "paid_problem"


def test_unknown_file_names_are_rejected(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    response = save(client, "free-01", {"../../etc/passwd": "x"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unknown_files"


def test_drafts_over_the_size_limit_are_rejected(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    response = save(client, "free-01", {"main.py": "x" * 1_000_001})

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "code_too_large"


def test_saving_needs_csrf(client: TestClient, db: Session) -> None:
    add_problem(db, "free-01")
    sign_in(client, db)

    response = client.put("/problems/free-01/draft", json={"files": {}})

    assert response.status_code == 403

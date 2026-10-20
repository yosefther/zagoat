from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningPath, Problem
from app.problems.loader import ProblemError, load_paths
from app.problems.sync import sync_from_dir
from tests.conftest import sign_in, submit_and_finish
from tests.problem_factory import add_problem, make_task_folder

REPO_PROBLEMS = Path(__file__).resolve().parents[2] / "problems"


def write_paths(root: Path, body: str) -> None:
    (root / "paths.yaml").write_text(body)


def test_repo_paths_are_valid() -> None:
    from app.problems.loader import load_all

    ids = {p.spec.id for p in load_all(REPO_PROBLEMS)}

    assert load_paths(REPO_PROBLEMS, ids)


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            "- id: a-path\n  title: A path\n  summary: Ten chars plus.\n  tasks: [nope-01]\n",
            "unknown tasks",
        ),
        (
            "- id: a-path\n  title: A path\n  summary: Ten chars plus.\n  tasks: [t-01, t-01]\n",
            "a task twice",
        ),
        (
            "- {id: a-path, title: A path, summary: Ten chars plus., tasks: [t-01]}\n"
            "- {id: a-path, title: Again, summary: Ten chars plus., tasks: [t-01]}\n",
            "used twice",
        ),
        ("- id: a-path\n  title: A path\n  summary: Ten chars plus.\n  tasks: []\n", "tasks"),
        ("id: not-a-list\n", "must be a list"),
    ],
)
def test_invalid_paths_are_rejected(tmp_path: Path, body: str, message: str) -> None:
    write_paths(tmp_path, body)

    with pytest.raises(ProblemError, match=message):
        load_paths(tmp_path, {"t-01"})


def test_sync_stores_paths_in_file_order(tmp_path: Path, db: Session) -> None:
    make_task_folder(tmp_path, "t-01")
    make_task_folder(tmp_path, "t-02")
    write_paths(
        tmp_path,
        "- {id: second, title: Second path, summary: Ten chars plus., tasks: [t-02, t-01]}\n"
        "- {id: first, title: First path, summary: Ten chars plus., tasks: [t-01]}\n",
    )

    report = sync_from_dir(db, tmp_path)

    assert report.paths == ["second", "first"]
    rows = db.scalars(select(LearningPath).order_by(LearningPath.position)).all()
    assert [(r.id, r.task_ids) for r in rows] == [("second", ["t-02", "t-01"]), ("first", ["t-01"])]

    write_paths(
        tmp_path, "- {id: first, title: First path, summary: Ten chars plus., tasks: [t-02]}\n"
    )
    sync_from_dir(db, tmp_path)
    assert [r.id for r in db.scalars(select(LearningPath))] == ["first"]


def test_bad_paths_file_changes_nothing(tmp_path: Path, db: Session) -> None:
    make_task_folder(tmp_path, "t-01")
    write_paths(tmp_path, "- {id: p, title: A path, summary: Ten chars plus., tasks: [missing]}\n")

    with pytest.raises(ProblemError):
        sync_from_dir(db, tmp_path)

    assert db.scalars(select(Problem)).all() == []


def add_path(db: Session, path_id: str, task_ids: list[str], position: int = 0) -> None:
    db.add(
        LearningPath(
            id=path_id,
            title=path_id.title(),
            summary="A path for tests.",
            position=position,
            task_ids=task_ids,
        )
    )
    db.commit()


def test_paths_list_tasks_in_order_for_visitors(client: TestClient, db: Session) -> None:
    add_problem(db, "a-01")
    add_problem(db, "b-01")
    add_path(db, "climb", ["b-01", "a-01"])

    body = client.get("/paths").json()

    assert [p["id"] for p in body] == ["climb"]
    assert [t["id"] for t in body[0]["tasks"]] == ["b-01", "a-01"]
    assert body[0]["solved"] == 0
    assert body[0]["next_task_id"] == "b-01"


def test_paths_show_progress_and_next_task(
    client: TestClient, worker: TestClient, db: Session
) -> None:
    add_problem(db, "a-01")
    add_problem(db, "b-01")
    add_path(db, "climb", ["a-01", "b-01"])
    sign_in(client, db)

    submit_and_finish(client, worker, "a-01", "passed")

    path = client.get("/paths/climb").json()
    assert path["solved"] == 1
    assert path["next_task_id"] == "b-01"
    assert path["tasks"][0]["progress"] == "solved"


def test_unpublished_tasks_drop_out_and_empty_paths_hide(client: TestClient, db: Session) -> None:
    add_problem(db, "a-01")
    hidden = add_problem(db, "b-01")
    hidden.published = False
    db.commit()
    add_path(db, "mixed", ["a-01", "b-01"])
    add_path(db, "empty", ["b-01"], position=1)

    body = client.get("/paths").json()

    assert [(p["id"], len(p["tasks"])) for p in body] == [("mixed", 1)]
    assert client.get("/paths/empty").status_code == 404


def test_unknown_path_is_404(client: TestClient) -> None:
    response = client.get("/paths/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "path_not_found"

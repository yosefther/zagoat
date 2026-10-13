import shutil
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem
from app.problems.loader import ProblemError, load_all, load_problem, split_hints
from app.problems.sync import sync_from_dir
from tests.problem_factory import make_task_folder

REPO_PROBLEMS = Path(__file__).resolve().parents[2] / "problems"


def test_repo_problems_are_valid() -> None:
    problems = load_all(REPO_PROBLEMS)

    assert {p.spec.id for p in problems} >= {"rag-chunking-01", "evals-ticket-classifier-01"}


def test_loader_reads_public_parts_only(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)

    problem = load_problem(folder)

    assert problem.starter_files == {
        "main.py": "def add(a, b):\n    return a - b\n",
        "util.py": "X = 1\n",
    }
    assert problem.hints == ["Look at the loop.", "Check the bounds."]
    assert problem.walkthrough == "Full solution.\n"
    assert "test_hidden" not in repr(problem)


def test_hints_split_on_level_two_headings() -> None:
    assert split_hints("# Hints\n\nintro\n\n## Hint 1\n\nA\n\n## Hint 2\n\nB\n") == ["A", "B"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda f: (f / "problem.yaml").write_text("id: test-task-01\n"), "problem.yaml"),
        (
            lambda f: (f / "problem.yaml").write_text(
                (f / "problem.yaml").read_text().replace("category: rag", "category: games")
            ),
            "category",
        ),
        (
            lambda f: (f / "problem.yaml").write_text(
                (f / "problem.yaml").read_text().replace("id: test-task-01", "id: other-id")
            ),
            "must match the folder name",
        ),
        (lambda f: (f / "statement.md").unlink(), "statement.md"),
        (lambda f: (f / "tests" / "hidden" / "test_hidden.py").unlink(), r"test_\*\.py"),
        (lambda f: (f / "reference" / "extra.py").write_text("x = 1\n"), "not in the starter"),
        (lambda f: (f / "starter" / "model.bin").write_bytes(b"\0"), "only text files"),
        (lambda f: (f / "hints.md").write_text("no headings here\n"), "## Hint 1"),
    ],
)
def test_invalid_tasks_are_rejected(tmp_path: Path, change: object, message: str) -> None:
    folder = make_task_folder(tmp_path)
    change(folder)  # type: ignore[operator]

    with pytest.raises(ProblemError, match=message):
        load_problem(folder)


def test_sync_creates_then_versions_then_unpublishes(tmp_path: Path, db: Session) -> None:
    folder = make_task_folder(tmp_path)

    first = sync_from_dir(db, tmp_path)
    assert first.created == ["test-task-01"]
    assert db.get(Problem, "test-task-01").version == 1  # type: ignore[union-attr]

    assert sync_from_dir(db, tmp_path).unchanged == ["test-task-01"]

    (folder / "tests" / "hidden" / "test_hidden.py").write_text("def test_y():\n    assert 1\n")
    assert sync_from_dir(db, tmp_path).updated == ["test-task-01"]
    assert db.get(Problem, "test-task-01").version == 2  # type: ignore[union-attr]

    shutil.rmtree(folder)
    assert sync_from_dir(db, tmp_path).unpublished == ["test-task-01"]
    row = db.scalars(select(Problem)).one()
    assert row.published is False

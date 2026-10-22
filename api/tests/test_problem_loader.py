import shutil
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Problem
from app.problems.loader import (
    MAX_PREVIEW_LINES,
    MAX_PREVIEW_WIDTH,
    ProblemError,
    load_all,
    load_problem,
    split_hints,
)
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


FEATURED = """\
featured:
  order: 2
  file: main.py
  lines: [{first}, {last}]
  checks: [Adds two numbers]
"""
GAUGE = """\
  gauge:
    metric: {metric}
    label: score
    starter_value: 0.3
"""
METRICS = """\
grader:
  metrics:
    - name: score
      threshold: 0.8
    - name: latency_ms
      threshold: 200
      goal: at_most
"""


def feature(folder: Path, first: int = 1, last: int = 2, gauge: str | None = None) -> None:
    spec = folder / "problem.yaml"
    block = FEATURED.format(first=first, last=last)
    if gauge:
        block += GAUGE.format(metric=gauge)
    spec.write_text(spec.read_text() + METRICS + block)


def test_featured_preview_quotes_the_starter_file(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    feature(folder, first=2, last=2, gauge="score")

    preview = load_problem(folder).featured

    assert preview == {
        "order": 2,
        "file": "main.py",
        "code": "return a - b",  # dedented
        "checks": ["Adds two numbers"],
        "gauge": {"label": "score", "threshold": 0.8, "starter_value": 0.3},
    }


def test_tasks_without_a_featured_block_are_not_featured(tmp_path: Path) -> None:
    assert load_problem(make_task_folder(tmp_path)).featured is None


@pytest.mark.parametrize(
    ("first", "last", "gauge", "message"),
    [
        (0, 1, None, "outside main.py"),
        (2, 1, None, "outside main.py"),
        (1, 3, None, "outside main.py"),
        (1, 2, "recall", "not a grader metric"),
        (1, 2, "latency_ms", "at_least metric"),
    ],
)
def test_invalid_featured_blocks_are_rejected(
    tmp_path: Path, first: int, last: int, gauge: str | None, message: str
) -> None:
    folder = make_task_folder(tmp_path)
    feature(folder, first=first, last=last, gauge=gauge)

    with pytest.raises(ProblemError, match=message):
        load_problem(folder)


def test_only_free_tasks_can_be_featured(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path, access="paid")
    feature(folder)

    with pytest.raises(ProblemError, match="only free tasks"):
        load_problem(folder)


def test_featured_checks_are_unique(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    feature(folder)
    spec = folder / "problem.yaml"
    spec.write_text(spec.read_text().replace("[Adds two numbers]", "[Adds two, Adds two]"))

    with pytest.raises(ProblemError, match="a check twice"):
        load_problem(folder)


def test_gauge_starter_value_is_below_the_threshold(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    feature(folder, gauge="score")
    spec = folder / "problem.yaml"
    spec.write_text(spec.read_text().replace("starter_value: 0.3", "starter_value: 0.8"))

    with pytest.raises(ProblemError, match="below the threshold"):
        load_problem(folder)


def test_featured_file_must_be_a_starter_file(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    feature(folder)
    spec = folder / "problem.yaml"
    spec.write_text(spec.read_text().replace("file: main.py", "file: secret.py"))

    with pytest.raises(ProblemError, match="not a starter file"):
        load_problem(folder)


def test_featured_preview_is_short(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    (folder / "starter" / "main.py").write_text("x = 1\n" * 40)
    feature(folder, first=1, last=MAX_PREVIEW_LINES + 1)

    with pytest.raises(ProblemError, match=f"more than {MAX_PREVIEW_LINES} lines"):
        load_problem(folder)


def test_featured_preview_lines_fit_the_code_box(tmp_path: Path) -> None:
    folder = make_task_folder(tmp_path)
    (folder / "starter" / "main.py").write_text("x = '" + "a" * MAX_PREVIEW_WIDTH + "'\n")
    feature(folder, first=1, last=1)

    with pytest.raises(ProblemError, match=f"keep them to {MAX_PREVIEW_WIDTH}"):
        load_problem(folder)


def test_sync_stores_and_clears_the_featured_preview(tmp_path: Path, db: Session) -> None:
    folder = make_task_folder(tmp_path)
    original = (folder / "problem.yaml").read_text()
    feature(folder)

    sync_from_dir(db, tmp_path)
    row = db.scalars(select(Problem)).one()
    assert row.featured is not None
    assert row.featured["code"] == "def add(a, b):\n    return a - b"

    (folder / "problem.yaml").write_text(original)
    sync_from_dir(db, tmp_path)
    db.refresh(row)
    assert row.featured is None


def test_reserved_ids_are_rejected(tmp_path: Path) -> None:
    make_task_folder(tmp_path, problem_id="featured")

    with pytest.raises(ProblemError, match="reserved"):
        load_problem(tmp_path / "featured")

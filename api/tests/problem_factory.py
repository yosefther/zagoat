"""Build small task folders and problem rows for tests."""

from pathlib import Path
from textwrap import dedent

from sqlalchemy.orm import Session

from app.models import Problem

PROBLEM_YAML = """\
id: {id}
title: A small test task
summary: A task used only by the API test suite.
category: rag
difficulty: easy
est_minutes: 30
access: {access}
image: zagoat-py312-ml
"""


def make_task_folder(root: Path, problem_id: str = "test-task-01", access: str = "free") -> Path:
    folder = root / problem_id
    (folder / "starter").mkdir(parents=True)
    (folder / "reference").mkdir()
    (folder / "data").mkdir()
    (folder / "tests" / "sample").mkdir(parents=True)
    (folder / "tests" / "hidden").mkdir(parents=True)
    (folder / "problem.yaml").write_text(PROBLEM_YAML.format(id=problem_id, access=access))
    (folder / "statement.md").write_text("Fix the function.\n")
    (folder / "hints.md").write_text(
        dedent("""\
            # Hints

            ## Hint 1

            Look at the loop.

            ## Hint 2

            Check the bounds.
            """)
    )
    (folder / "walkthrough.md").write_text("Full solution.\n")
    (folder / "starter" / "main.py").write_text("def add(a, b):\n    return a - b\n")
    (folder / "starter" / "util.py").write_text("X = 1\n")
    (folder / "reference" / "main.py").write_text("def add(a, b):\n    return a + b\n")
    (folder / "tests" / "sample" / "test_sample.py").write_text("def test_x():\n    pass\n")
    (folder / "tests" / "hidden" / "test_hidden.py").write_text("def test_y():\n    pass\n")
    return folder


def add_problem(db: Session, problem_id: str = "test-task-01", access: str = "free") -> Problem:
    problem = Problem(
        id=problem_id,
        title=f"Task {problem_id}",
        summary="A task used only by the API test suite.",
        category="rag",
        difficulty="easy",
        est_minutes=30,
        access=access,
        version=1,
        content_hash="0" * 64,
        published=True,
        statement="Fix the function.",
        starter_files={"main.py": "def add(a, b):\n    return a - b\n", "util.py": "X = 1\n"},
        hints=["Look at the loop.", "Check the bounds."],
        walkthrough="Full solution.",
        reference_files={"main.py": "def add(a, b):\n    return a + b\n"},
        metrics=[{"name": "score", "threshold": 0.8, "goal": "at_least"}],
    )
    db.add(problem)
    db.commit()
    return problem

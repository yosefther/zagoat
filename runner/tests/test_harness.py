"""Run the real harness through LocalExecutor on tiny throwaway tasks."""

import sys
from pathlib import Path

import pytest

from zagoat_runner.config import get_settings
from zagoat_runner.executor import Job, LocalExecutor, write_files
from zagoat_runner.grading import Kind, Outcome, grade
from zagoat_runner.taskspec import load_task

HIDDEN_TEST = '''
from main import add
from zagoat import record_metric


def test_adds_small_numbers():
    """Adds small numbers"""
    secret_expected = 5
    assert add(2, 3) == secret_expected, "add(2, 3) should be 5"


def test_records_metric():
    record_metric("score", 0.9 if add(1, 1) == 2 else 0.0)
'''


@pytest.fixture
def task_root(tmp_path: Path) -> Path:
    root = tmp_path / "tiny-01"
    write_files(
        root,
        {
            "problem.yaml": (
                "id: tiny-01\nimage: x\ngrader:\n  metrics:\n"
                "    - name: score\n      threshold: 0.8\n"
            ),
            "starter/main.py": "def add(a, b):\n    return a - b\n",
            "reference/main.py": "def add(a, b):\n    return a + b\n",
            "data/.keep": "",
            "tests/sample/test_sample.py": (
                "from main import add\n\n\ndef test_sample():\n    print('hello from sample')\n"
                "    assert add(1, 1) == 2\n"
            ),
            "tests/hidden/test_hidden.py": HIDDEN_TEST,
        },
    )
    return root


def execute(task_root: Path, kind: Kind, main_py: str, time_limit: int = 30) -> Outcome:
    settings = get_settings()
    task = load_task(task_root)
    executor = LocalExecutor(
        harness_dir=settings.harness_dir,
        llm_base_url="http://127.0.0.1:9/v1",
        python=sys.executable,
    )
    job = Job(task=task, kind=kind, files={"main.py": main_py}, llm_key="zagoat-tiny-01-x")
    return grade(
        executor.execute(job, time_limit),
        kind,
        task.metrics,
        time_limit_seconds=time_limit,
        memory_limit_mb=2048,
        output_limit_bytes=1024,
    )


def test_reference_passes(task_root: Path) -> None:
    outcome = execute(task_root, "submit", "def add(a, b):\n    return a + b\n")

    assert outcome.verdict == "passed"
    assert outcome.metrics[0]["value"] == 0.9


def test_submit_shows_author_message_but_not_test_source(task_root: Path) -> None:
    outcome = execute(task_root, "submit", "def add(a, b):\n    return a - b\n")

    assert outcome.verdict == "failed"
    failed = next(t for t in outcome.tests if t["outcome"] == "failed")
    assert failed == {
        "name": "Adds small numbers",
        "outcome": "failed",
        "message": "add(2, 3) should be 5",
    }
    assert "secret_expected" not in repr(outcome)
    assert outcome.stdout is None


def test_exception_in_user_code_points_at_user_file(task_root: Path) -> None:
    outcome = execute(task_root, "submit", "def add(a, b):\n    return a / 0\n")

    assert outcome.verdict == "error"
    assert "ZeroDivisionError" in (outcome.message or "")
    assert "main.py, line 2" in (outcome.message or "")


def test_syntax_error_is_an_import_error(task_root: Path) -> None:
    outcome = execute(task_root, "submit", "def add(a, b)\n    return a + b\n")

    assert outcome.verdict == "error"
    assert "failed to import" in (outcome.message or "")


def test_hard_exit_is_an_error(task_root: Path) -> None:
    outcome = execute(task_root, "submit", "import os\n\ndef add(a, b):\n    os._exit(0)\n")

    assert outcome.verdict == "error"


def test_time_limit(task_root: Path) -> None:
    outcome = execute(
        task_root, "submit", "def add(a, b):\n    while True:\n        pass\n", time_limit=2
    )

    assert outcome.verdict == "time_limit"


def test_run_uses_sample_tests_and_shows_output(task_root: Path) -> None:
    outcome = execute(task_root, "run", "def add(a, b):\n    return a + b\n")

    assert outcome.verdict == "passed"
    assert outcome.tests_total == 1
    assert "1 passed" in (outcome.stdout or "")
    assert "hello from sample" in (outcome.stdout or "")

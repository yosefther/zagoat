from typing import Any

import pytest

from zagoat_runner.grading import ExecResult, Kind, Outcome, grade, truncate
from zagoat_runner.taskspec import MetricSpec

METRICS = (MetricSpec("recall_at_5", 0.8),)


def results(*outcomes: str, metrics: dict[str, float] | None = None, **extra: Any) -> ExecResult:
    tests = [
        {"name": f"t{i}", "outcome": o, "message": None if o == "passed" else "msg"}
        for i, o in enumerate(outcomes)
    ]
    payload = {"tests": tests, "metrics": metrics or {}, "collection_errors": []}
    payload.update(extra)
    return ExecResult(exit_code=0, duration_ms=10, stdout="out", stderr="err", results=payload)


def run(
    result: ExecResult, kind: Kind = "submit", metrics: tuple[MetricSpec, ...] = METRICS
) -> Outcome:
    return grade(
        result,
        kind,
        metrics,
        time_limit_seconds=120,
        memory_limit_mb=2048,
        output_limit_bytes=64 * 1024,
    )


def test_passed_needs_every_test_and_metric() -> None:
    outcome = run(results("passed", "passed", metrics={"recall_at_5": 0.85}))

    assert outcome.verdict == "passed"
    assert (outcome.tests_passed, outcome.tests_total) == (2, 2)
    assert outcome.metrics[0]["met"] is True


def test_a_failing_test_fails() -> None:
    outcome = run(results("passed", "failed", metrics={"recall_at_5": 0.9}))

    assert outcome.verdict == "failed"
    assert outcome.message == "1 of 2 tests failed."


def test_a_missed_metric_fails_even_when_tests_pass() -> None:
    outcome = run(results("passed", metrics={"recall_at_5": 0.5}))

    assert outcome.verdict == "failed"
    assert outcome.metrics[0] == {
        "name": "recall_at_5",
        "value": 0.5,
        "threshold": 0.8,
        "goal": "at_least",
        "met": False,
    }


def test_a_missing_metric_fails() -> None:
    assert run(results("passed")).verdict == "failed"


def test_at_most_metrics_must_stay_under_the_threshold() -> None:
    latency = (MetricSpec("p95_ms", 200, "at_most"),)

    assert run(results("passed", metrics={"p95_ms": 150}), metrics=latency).verdict == "passed"
    assert run(results("passed", metrics={"p95_ms": 250}), metrics=latency).verdict == "failed"


def test_an_exception_in_user_code_is_an_error() -> None:
    outcome = run(results("passed", "error", metrics={"recall_at_5": 0.9}))

    assert outcome.verdict == "error"
    assert outcome.message == "Your code raised an exception: msg"


def test_import_failure_is_an_error() -> None:
    outcome = run(results(collection_errors=["SyntaxError: bad (in main.py, line 3)"]))

    assert outcome.verdict == "error"
    assert "SyntaxError" in (outcome.message or "")


def test_no_results_file_is_an_error() -> None:
    outcome = run(ExecResult(exit_code=-9, duration_ms=5))

    assert outcome.verdict == "error"


@pytest.mark.parametrize(
    ("result", "verdict"),
    [
        (ExecResult(exit_code=None, duration_ms=120_000, timed_out=True), "time_limit"),
        (ExecResult(exit_code=137, duration_ms=500, oom_killed=True), "memory_limit"),
        (ExecResult(exit_code=None, duration_ms=0, system_error="image missing"), "system_error"),
    ],
)
def test_limits_and_system_errors(result: ExecResult, verdict: str) -> None:
    assert run(result).verdict == verdict


def test_submit_never_shows_output() -> None:
    outcome = run(results("passed", metrics={"recall_at_5": 0.9}), kind="submit")

    assert outcome.stdout is None
    assert outcome.stderr is None


def test_run_shows_output_and_ignores_thresholds() -> None:
    outcome = run(results("passed", metrics={"sample_recall": 0.5}), kind="run")

    assert outcome.verdict == "passed"
    assert outcome.stdout == "out"
    assert outcome.metrics == [
        {"name": "sample_recall", "value": 0.5, "threshold": None, "goal": None, "met": None}
    ]


def test_output_is_truncated_to_the_limit() -> None:
    text = truncate("é" * 100, 11)

    assert text.startswith("ééééé")
    assert text.endswith("output truncated")

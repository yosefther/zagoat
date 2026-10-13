"""Turn what happened in the sandbox into a verdict and the result the user sees.

This runs in the worker, outside the sandbox. The harness inside the sandbox only reports
test outcomes and metrics (brief, section 5: verdicts).
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from zagoat_runner.taskspec import MetricSpec

Kind = Literal["run", "submit"]
Verdict = Literal["passed", "failed", "error", "time_limit", "memory_limit", "system_error"]


@dataclass(frozen=True)
class ExecResult:
    """What an executor observed. `results` is the harness JSON, if it wrote one."""

    exit_code: int | None
    duration_ms: int
    timed_out: bool = False
    oom_killed: bool = False
    stdout: str = ""
    stderr: str = ""
    results: dict[str, Any] | None = None
    system_error: str | None = None


@dataclass
class Outcome:
    verdict: Verdict
    message: str | None
    tests_passed: int
    tests_total: int
    tests: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    stdout: str | None = None
    stderr: str | None = None


def truncate(text: str, limit_bytes: int) -> str:
    data = text.encode("utf-8", errors="replace")
    if len(data) <= limit_bytes:
        return text
    return data[:limit_bytes].decode("utf-8", errors="ignore") + "\n… output truncated"


def _metric_rows(
    specs: tuple[MetricSpec, ...], recorded: dict[str, float], kind: Kind
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        value = recorded.get(spec.name)
        rows.append(
            {
                "name": spec.name,
                "value": value,
                "threshold": spec.threshold,
                "goal": spec.goal,
                "met": value is not None and spec.met(value),
            }
        )
    if kind == "run":
        # Sample tests may record extra metrics; show them without a threshold.
        known = {spec.name for spec in specs}
        rows += [
            {"name": name, "value": value, "threshold": None, "goal": None, "met": None}
            for name, value in sorted(recorded.items())
            if name not in known
        ]
    return rows


def grade(
    result: ExecResult,
    kind: Kind,
    metrics: tuple[MetricSpec, ...],
    *,
    time_limit_seconds: int,
    memory_limit_mb: int,
    output_limit_bytes: int,
) -> Outcome:
    # Run shows the program's output; Submit shows only test names, messages and metrics.
    show_output = kind == "run"
    stdout = truncate(result.stdout, output_limit_bytes) if show_output else None
    stderr = truncate(result.stderr, output_limit_bytes) if show_output else None

    def outcome(verdict: Verdict, message: str | None, **extra: Any) -> Outcome:
        return Outcome(verdict, message, stdout=stdout, stderr=stderr, **extra)

    if result.system_error:
        return outcome(
            "system_error",
            "Something went wrong on our side. This attempt doesn't count. Try again.",
            tests_passed=0,
            tests_total=0,
        )
    if result.timed_out:
        return outcome(
            "time_limit",
            f"Your code took longer than {time_limit_seconds} seconds. Look for slow loops "
            "or repeated work.",
            tests_passed=0,
            tests_total=0,
        )
    if result.oom_killed:
        return outcome(
            "memory_limit",
            f"Your code used more than {memory_limit_mb // 1024} GB of memory. Avoid loading "
            "everything at once.",
            tests_passed=0,
            tests_total=0,
        )
    if result.results is None:
        return outcome(
            "error",
            "Your code stopped the test run before it finished (for example by calling "
            "os._exit or crashing the interpreter).",
            tests_passed=0,
            tests_total=0,
        )

    tests: list[dict[str, Any]] = list(result.results.get("tests", []))
    recorded = {str(k): float(v) for k, v in result.results.get("metrics", {}).items()}
    metric_rows = _metric_rows(metrics if kind == "submit" else (), recorded, kind)
    passed = sum(1 for t in tests if t["outcome"] == "passed")
    collection_errors: list[str] = list(result.results.get("collection_errors", []))
    common = {
        "tests_passed": passed,
        "tests_total": len(tests),
        "tests": tests,
        "metrics": metric_rows,
    }

    if collection_errors:
        return outcome("error", f"Your code failed to import: {collection_errors[0]}", **common)
    errored = next((t for t in tests if t["outcome"] == "error"), None)
    if errored:
        return outcome("error", f"Your code raised an exception: {errored['message']}", **common)
    if not tests:
        return outcome("error", "No tests ran. Check that your files import cleanly.", **common)
    failed_tests = len(tests) - passed
    missed = [row for row in metric_rows if row["met"] is False]
    if failed_tests or missed:
        parts = []
        if failed_tests:
            parts.append(f"{failed_tests} of {len(tests)} tests failed")
        if missed:
            parts.append(f"{len(missed)} metric(s) missed the target")
        return outcome("failed", "; ".join(parts).capitalize() + ".", **common)
    return outcome("passed", f"All {len(tests)} tests passed.", **common)

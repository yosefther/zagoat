"""pytest plugin that records each test's outcome and an author-written message.

For Submit (hidden tests) pytest runs with --assert=plain, so an AssertionError carries
only the message the task author wrote, never the hidden test's source or values.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from zagoat import _state

MAX_MESSAGE_CHARS = 2000

_results: dict[str, dict[str, Any]] = {}
_collection_errors: list[str] = []


def _work_dir() -> Path:
    return Path(os.environ.get("ZAGOAT_WORK", os.getcwd())).resolve()


def _display_name(item: pytest.Item) -> str:
    doc = getattr(getattr(item, "function", None), "__doc__", None)
    if doc and doc.strip():
        name = doc.strip().splitlines()[0]
    else:
        words = item.name.split("[")[0].removeprefix("test_").replace("_", " ")
        name = words[:1].upper() + words[1:]
    callspec = getattr(item, "callspec", None)
    if callspec is not None and callspec.params:
        params = ", ".join(f"{key}={value!r}" for key, value in callspec.params.items())
        name = f"{name} ({params})"
    return name


def _assertion_text(exc: AssertionError) -> str:
    """The author's message, plus the first line of pytest's explanation if there is one."""
    text = str(exc).strip()
    if not text:
        return "This check failed."
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("assert "):
            return "\n".join(lines[: index + 1])
    return text


def _user_location(excinfo: pytest.ExceptionInfo[BaseException]) -> str | None:
    """The last traceback frame inside the user's files, as 'file.py, line N'."""
    work = _work_dir()
    location = None
    for entry in excinfo.traceback:
        path = Path(str(entry.path)).resolve()
        if path.is_relative_to(work):
            location = f"{path.relative_to(work).as_posix()}, line {entry.lineno + 1}"
    return location


def _message(excinfo: pytest.ExceptionInfo[BaseException]) -> tuple[str, str]:
    exc = excinfo.value
    if isinstance(exc, AssertionError):
        return "failed", _assertion_text(exc)[:MAX_MESSAGE_CHARS]
    text = f"{type(exc).__name__}: {exc}".strip()
    location = _user_location(excinfo)
    if location:
        text = f"{text} (in {location})"
    return "error", text[:MAX_MESSAGE_CHARS]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Any:
    outcome = yield
    report = outcome.get_result()
    entry = _results.setdefault(
        item.nodeid, {"name": _display_name(item), "outcome": "passed", "message": None}
    )
    if report.skipped and report.when in ("setup", "call"):
        entry["outcome"] = "skipped"
    elif report.failed and call.excinfo is not None and entry["outcome"] == "passed":
        entry["outcome"], entry["message"] = _message(call.excinfo)


def pytest_collectreport(report: pytest.CollectReport) -> None:
    if not report.failed:
        return
    crash = getattr(report.longrepr, "reprcrash", None)
    message = getattr(crash, "message", None) or "Your code could not be imported."
    path = getattr(crash, "path", None)
    if path:
        resolved = Path(path).resolve()
        work = _work_dir()
        if resolved.is_relative_to(work):
            message = f"{message} (in {resolved.relative_to(work).as_posix()}, line {crash.lineno})"
    _collection_errors.append(message[:MAX_MESSAGE_CHARS])


def pytest_sessionfinish(session: pytest.Session) -> None:
    out = os.environ.get("ZAGOAT_RESULTS")
    if not out:
        return
    payload = {
        "tests": list(_results.values()),
        "metrics": dict(_state.METRICS),
        "collection_errors": _collection_errors,
    }
    Path(out).write_text(json.dumps(payload))

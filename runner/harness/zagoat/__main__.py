"""Run a task's tests against the user's code.

    python -m zagoat run|submit TESTS_DIR

Results go to the JSON file named by $ZAGOAT_RESULTS.
"""

import io
import json
import os
import re
import sys
from pathlib import Path

import pytest

EXCEPTION_LINE = re.compile(r"^(?:E\s+)?([A-Za-z_][\w.]*(?:Error|Exception|Exit)\b.*)$")
USER_FRAME = re.compile(r'File "([^"]+)", line (\d+)')


class Tee(io.TextIOBase):
    """Write to the real stream and keep a copy."""

    def __init__(self, stream: io.TextIOBase) -> None:
        self.stream = stream
        self.copy = io.StringIO()

    def write(self, text: str) -> int:
        self.copy.write(text)
        return self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()


def startup_error(output: str) -> str:
    """Summarize an error that stopped pytest before any test ran (e.g. in conftest.py)."""
    work = Path(os.environ.get("ZAGOAT_WORK", os.getcwd())).resolve()
    exception = None
    location = None
    for line in output.splitlines():
        match = EXCEPTION_LINE.match(line.strip())
        if match:
            exception = match.group(1)
        frame = USER_FRAME.search(line)
        if frame and Path(frame.group(1)).resolve().is_relative_to(work):
            location = f"{Path(frame.group(1)).resolve().relative_to(work)}, line {frame.group(2)}"
    message = exception or "Your code could not be imported."
    return f"{message} (in {location})" if location else message


def main() -> int:
    mode, tests_dir = sys.argv[1], sys.argv[2]
    # Test folders may hold helper modules next to the tests (e.g. rag_helpers.py).
    sys.path.append(tests_dir)
    args = [
        tests_dir,
        "-p", "zagoat.plugin",
        "-p", "no:cacheprovider",
        "--import-mode=importlib",
        "-o", "python_files=test_*.py",
        "--rootdir", tests_dir,
    ]
    if mode == "submit":
        # Hidden tests: keep assertion messages to what the author wrote, print nothing.
        args += ["--assert=plain", "-p", "no:terminal"]
    else:
        # Run: show the user's own print() output alongside the sample test results.
        args += ["-q", "-s", "--tb=short", "--no-header"]

    stderr = Tee(sys.stderr)  # type: ignore[arg-type]
    sys.stderr = stderr
    try:
        code = int(pytest.main(args))
    finally:
        sys.stderr = stderr.stream  # type: ignore[assignment]

    results = os.environ.get("ZAGOAT_RESULTS")
    if results and not Path(results).exists():
        payload = {
            "tests": [],
            "metrics": {},
            "collection_errors": [startup_error(stderr.copy.getvalue())],
        }
        Path(results).write_text(json.dumps(payload))
    return code


if __name__ == "__main__":
    sys.exit(main())

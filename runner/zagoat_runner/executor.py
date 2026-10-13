"""Executors run user code against a task's tests and report what happened.

`LocalExecutor` runs the harness in a plain subprocess. It has no isolation and is only for
CI task validation and tests. The sandboxed Docker/gVisor executor implements the same
interface.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from zagoat_runner.grading import ExecResult, Kind
from zagoat_runner.taskspec import TaskSpec


@dataclass(frozen=True)
class Job:
    task: TaskSpec
    kind: Kind
    files: dict[str, str]
    llm_key: str


class Executor(Protocol):
    def execute(self, job: Job, time_limit_seconds: int) -> ExecResult: ...


def write_files(folder: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError(f"file name escapes the work folder: {name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


@dataclass(frozen=True)
class LocalExecutor:
    harness_dir: Path
    llm_base_url: str
    python: str = sys.executable

    def execute(self, job: Job, time_limit_seconds: int) -> ExecResult:
        tests_dir = job.task.sample_tests if job.kind == "run" else job.task.hidden_tests
        with tempfile.TemporaryDirectory(prefix="zagoat-job-") as tmp:
            work = Path(tmp) / "work"
            work.mkdir()
            write_files(work, job.files)
            results_path = Path(tmp) / "results.json"
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": tmp,
                "PYTHONPATH": os.pathsep.join([str(self.harness_dir), str(work)]),
                "PYTHONDONTWRITEBYTECODE": "1",
                "ZAGOAT_WORK": str(work),
                "ZAGOAT_DATA": str(job.task.data_dir or work / "data"),
                "ZAGOAT_RESULTS": str(results_path),
                "OPENAI_BASE_URL": self.llm_base_url,
                "OPENAI_API_KEY": job.llm_key,
            }
            started = time.monotonic()
            try:
                completed = subprocess.run(  # noqa: S603
                    [self.python, "-m", "zagoat", job.kind, str(tests_dir)],
                    cwd=work,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=time_limit_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return ExecResult(
                    exit_code=None,
                    duration_ms=int((time.monotonic() - started) * 1000),
                    timed_out=True,
                    stdout=_text(exc.stdout),
                    stderr=_text(exc.stderr),
                )
            duration_ms = int((time.monotonic() - started) * 1000)
            results = json.loads(results_path.read_text()) if results_path.exists() else None
            return ExecResult(
                exit_code=completed.returncode,
                duration_ms=duration_ms,
                stdout=completed.stdout,
                stderr=completed.stderr,
                results=results,
            )


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value

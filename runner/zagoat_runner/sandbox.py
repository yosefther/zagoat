"""Docker sandbox executor (brief, section 5).

Every job gets a fresh container that is removed when the job ends: gVisor runtime, non-root
user, no Linux capabilities, no-new-privileges, read-only root, a size-capped /tmp, CPU,
memory and process limits, and an internal network shared only with the mock LLM. Task data
and tests are mounted read-only; no secrets enter the container.
"""

import json
import logging
import os
import shutil
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from zagoat_runner.config import Settings
from zagoat_runner.executor import Job, write_files
from zagoat_runner.grading import ExecResult

log = logging.getLogger(__name__)


class SandboxUnavailableError(RuntimeError):
    """The sandbox can't run safely here (for example gVisor is missing in production)."""


def gvisor_available(settings: Settings) -> bool:
    try:
        output = subprocess.run(  # noqa: S603
            [settings.docker_binary, "info", "--format", "{{json .Runtimes}}"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise SandboxUnavailableError(f"Docker is not reachable: {exc}") from exc
    return "runsc" in json.loads(output or "{}")


def check_runtime(settings: Settings) -> bool:
    """Return whether to use gVisor. Production refuses to run without it."""
    if gvisor_available(settings):
        return True
    if settings.is_production:
        raise SandboxUnavailableError("gVisor (runsc) is not installed; refusing to run user code.")
    log.warning(
        "\n%s\n  gVisor (runsc) is not installed. Sandboxes use Docker's default runtime.\n"
        "  That is acceptable for local development only. Production refuses to start.\n%s",
        "!" * 78,
        "!" * 78,
    )
    return False


@dataclass(frozen=True)
class DockerExecutor:
    settings: Settings
    use_gvisor: bool

    def _docker(self, *args: str, timeout: float = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603
            [self.settings.docker_binary, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def command(self, job: Job, name: str, work: Path, out: Path) -> list[str]:
        settings = self.settings
        tests = job.task.sample_tests if job.kind == "run" else job.task.hidden_tests
        image = settings.images.get(job.task.image)
        if image is None:
            raise SandboxUnavailableError(f"No image configured for {job.task.image!r}")
        mounts = ["-v", f"{work}:/work:ro", "-v", f"{tests}:/task/tests:ro", "-v", f"{out}:/out:rw"]
        if job.task.data_dir and job.task.data_dir.is_dir():
            mounts += ["-v", f"{job.task.data_dir}:/task/data:ro"]
        env = {
            "OPENAI_BASE_URL": settings.sandbox_llm_base_url,
            "OPENAI_API_KEY": job.llm_key,
            "ZAGOAT_DATA": "/task/data",
            "ZAGOAT_WORK": "/work",
            "ZAGOAT_RESULTS": "/out/results.json",
            "PYTHONPATH": "/opt/zagoat:/work",
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": "/tmp",  # noqa: S108 (inside the container)
        }
        return [
            "run",
            "--detach",
            "--name", name,
            *(["--runtime", "runsc"] if self.use_gvisor else []),
            "--network", settings.sandbox_network,
            "--cpus", str(settings.cpus),
            "--memory", f"{settings.memory_limit_mb}m",
            "--memory-swap", f"{settings.memory_limit_mb}m",
            "--pids-limit", str(settings.pids_limit),
            "--read-only",
            "--tmpfs", f"/tmp:rw,nosuid,nodev,size={settings.tmp_size_mb}m",  # noqa: S108
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--user", settings.sandbox_user,
            "--log-driver", "json-file",
            "--log-opt", "max-size=1m",
            *mounts,
            *[part for key, value in env.items() for part in ("-e", f"{key}={value}")],
            "--workdir", "/work",
            image,
            "python", "-m", "zagoat", job.kind, "/task/tests",
        ]  # fmt: skip

    def execute(self, job: Job, time_limit_seconds: int) -> ExecResult:
        settings = self.settings
        job_id = job.llm_key.rsplit("-", 1)[-1]
        name = f"zagoat-job-{job_id}"
        job_dir = settings.jobs_dir / job_id
        work, out = job_dir / "work", job_dir / "out"
        started = time.monotonic()
        try:
            work.mkdir(parents=True)
            out.mkdir()
            write_files(work, job.files)
            # The sandbox user must read the code and write results.
            for path in [job_dir, work, *work.rglob("*")]:
                path.chmod(0o755 if path.is_dir() else 0o644)
            out.chmod(0o777)
            launched = self._docker(*self.command(job, name, work, out), timeout=60)
            if launched.returncode != 0:
                return self._system_error(started, f"docker run failed: {launched.stderr[-500:]}")
            timed_out = False
            try:
                self._docker(
                    "wait", name, timeout=time_limit_seconds + settings.startup_grace_seconds
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                self._docker("kill", name)
            duration_ms = int((time.monotonic() - started) * 1000)
            state = json.loads(self._docker("inspect", "-f", "{{json .State}}", name).stdout)
            logs = self._docker("logs", name)
            exit_code = state.get("ExitCode")
            # gVisor doesn't always set OOMKilled; a SIGKILL we didn't send is the OOM killer.
            oom = bool(state.get("OOMKilled")) or (exit_code == 137 and not timed_out)
            return ExecResult(
                exit_code=exit_code,
                duration_ms=duration_ms,
                timed_out=timed_out,
                oom_killed=oom and not timed_out,
                stdout=logs.stdout,
                stderr=logs.stderr,
                results=self._read_results(out / "results.json"),
            )
        except (
            OSError,
            subprocess.SubprocessError,
            json.JSONDecodeError,
            SandboxUnavailableError,
        ) as exc:
            return self._system_error(started, f"{type(exc).__name__}: {exc}")
        finally:
            self._docker("rm", "--force", "--volumes", name)
            shutil.rmtree(job_dir, ignore_errors=True)

    def _read_results(self, path: Path) -> dict[str, object] | None:
        # /out is writable by user code, so never follow a link it planted there: a symlink
        # to a host file would make the worker read that file.
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except OSError:
            return None
        with os.fdopen(fd, "rb") as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > self.settings.max_results_bytes:
                return None
            raw = file.read(self.settings.max_results_bytes + 1)
        try:
            data = json.loads(raw.decode())
        except (ValueError, UnicodeDecodeError):
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _system_error(started: float, detail: str) -> ExecResult:
        log.error("sandbox system error: %s", detail)
        return ExecResult(
            exit_code=None,
            duration_ms=int((time.monotonic() - started) * 1000),
            system_error=detail,
        )

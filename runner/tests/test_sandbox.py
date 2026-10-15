"""Sandbox hardening tests against real containers.

They need Docker, the zagoat-py312-ml:dev image and the mock LLM on the zagoat-sandbox
network (docker compose up mockllm). Set ZAGOAT_SANDBOX_TESTS=1 to run them.
"""

import os
import secrets
from pathlib import Path

import pytest

from zagoat_runner.config import get_settings
from zagoat_runner.executor import Job, write_files
from zagoat_runner.grading import Kind, Outcome, grade
from zagoat_runner.sandbox import DockerExecutor, check_runtime
from zagoat_runner.taskspec import load_task

pytestmark = pytest.mark.skipif(
    os.environ.get("ZAGOAT_SANDBOX_TESTS") != "1", reason="set ZAGOAT_SANDBOX_TESTS=1"
)

HIDDEN = '''
from main import probe


def test_probe():
    """Probe"""
    result = probe()
    assert result == "ok", f"probe said: {result}"
'''


@pytest.fixture(scope="module")
def executor() -> DockerExecutor:
    settings = get_settings()
    return DockerExecutor(settings, check_runtime(settings))


@pytest.fixture
def task_root(tmp_path: Path) -> Path:
    root = tmp_path / "probe-01"
    write_files(
        root,
        {
            "problem.yaml": "id: probe-01\nimage: zagoat-py312-ml\n",
            "starter/main.py": "def probe():\n    return 'starter'\n",
            "reference/main.py": "def probe():\n    return 'ok'\n",
            "data/info.txt": "data file\n",
            "tests/sample/test_sample.py": "import os\n\ndef test_listing():\n"
            "    print(sorted(os.listdir('/task/tests')))\n",
            "tests/hidden/test_hidden.py": HIDDEN,
        },
    )
    for path in [root, *root.rglob("*")]:
        path.chmod(0o755 if path.is_dir() else 0o644)
    return root


def run(
    executor: DockerExecutor, root: Path, code: str, kind: Kind = "submit", limit: int = 30
) -> Outcome:
    task = load_task(root)
    job = Job(task, kind, {"main.py": code}, f"zagoat-probe-01-{secrets.token_hex(6)}")
    return grade(
        executor.execute(job, limit),
        kind,
        task.metrics,
        time_limit_seconds=limit,
        memory_limit_mb=2048,
        output_limit_bytes=65536,
    )


def probe(body: str) -> str:
    lines = "\n".join(f"    {line}" for line in body.strip().splitlines())
    return f"def probe():\n{lines}\n"


def test_reference_passes(executor: DockerExecutor, task_root: Path) -> None:
    assert run(executor, task_root, probe("return 'ok'")).verdict == "passed"


def test_no_internet(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
import socket
try:
    socket.create_connection(("1.1.1.1", 80), timeout=3)
    return "reached the internet"
except OSError:
    return "ok"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_mock_llm_is_reachable(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
from openai import OpenAI
reply = OpenAI().chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
return "ok" if reply.choices[0].message.content else "no reply"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_non_root_without_capabilities(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
import os
caps = [l for l in open("/proc/self/status") if l.startswith("CapEff")][0].split()[1]
if os.getuid() == 0:
    return "running as root"
return "ok" if int(caps, 16) == 0 else f"capabilities {caps}"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_read_only_except_tmp(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
for path in ["/work/x.txt", "/task/data/x.txt", "/usr/x.txt"]:
    try:
        open(path, "w").write("x")
        return f"wrote {path}"
    except OSError:
        pass
open("/tmp/x.txt", "w").write("x")
return "ok"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_no_secrets_in_environment(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
import os
leaked = [k for k in os.environ if "SECRET" in k or "DATABASE" in k or k.startswith("REDIS")]
return "ok" if not leaked else f"leaked {leaked}"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_memory_limit(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
blocks = []
for _ in range(40):
    blocks.append(bytearray(100 * 1024 * 1024))
return "ok"
""")
    assert run(executor, task_root, code).verdict == "memory_limit"


def test_time_limit(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("while True:\n    pass")
    assert run(executor, task_root, code, limit=3).verdict == "time_limit"


def test_process_limit(executor: DockerExecutor, task_root: Path) -> None:
    code = probe("""
import subprocess
procs = []
try:
    for _ in range(200):
        procs.append(subprocess.Popen(["sleep", "5"]))
except OSError:
    return "ok"
finally:
    for p in procs:
        p.kill()
return f"started {len(procs)} processes"
""")
    assert run(executor, task_root, code).verdict == "passed"


def test_run_never_sees_hidden_tests(executor: DockerExecutor, task_root: Path) -> None:
    outcome = run(executor, task_root, probe("return 'ok'"), kind="run")

    assert "test_sample.py" in (outcome.stdout or "")
    assert "test_hidden" not in (outcome.stdout or "")

"""Reading the results file that sandboxed code can write to (no Docker needed)."""

import json
import os
from pathlib import Path

import pytest

from zagoat_runner.config import get_settings
from zagoat_runner.sandbox import DockerExecutor

RESULTS = {"tests": [{"name": "t", "outcome": "passed"}], "metrics": {}}


@pytest.fixture
def executor() -> DockerExecutor:
    return DockerExecutor(get_settings(), use_gvisor=False)


def test_reads_a_regular_results_file(executor: DockerExecutor, tmp_path: Path) -> None:
    path = tmp_path / "results.json"
    path.write_text(json.dumps(RESULTS))

    assert executor._read_results(path) == RESULTS


def test_ignores_a_symlink_planted_by_user_code(executor: DockerExecutor, tmp_path: Path) -> None:
    host_file = tmp_path / "host-secret.json"
    host_file.write_text(json.dumps(RESULTS))
    out = tmp_path / "out"
    out.mkdir()
    (out / "results.json").symlink_to(host_file)

    assert executor._read_results(out / "results.json") is None


def test_ignores_non_files_and_oversized_results(executor: DockerExecutor, tmp_path: Path) -> None:
    fifo = tmp_path / "fifo.json"
    os.mkfifo(fifo)
    big = tmp_path / "big.json"
    big.write_text(" " * (get_settings().max_results_bytes + 1) + "{}")

    assert executor._read_results(fifo) is None
    assert executor._read_results(big) is None
    assert executor._read_results(tmp_path / "missing.json") is None

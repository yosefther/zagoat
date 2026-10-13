"""Helpers available to task code and tests inside the sandbox.

    from zagoat import data_path, record_metric, llm_calls

This package has no third-party dependencies so it runs in any task image.
"""

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from zagoat import _state

__all__ = ["data_path", "llm_calls", "record_metric"]


def data_path(*parts: str) -> Path:
    """Path to a file in the task's read-only data folder."""
    return Path(os.environ.get("ZAGOAT_DATA", "data")).joinpath(*parts)


def record_metric(name: str, value: float) -> None:
    """Record a metric. Graders compare it with the threshold in problem.yaml."""
    _state.METRICS[name] = float(value)


def llm_calls() -> list[dict[str, Any]]:
    """Every call this job made to the mock LLM, oldest first."""
    base = os.environ["OPENAI_BASE_URL"].rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    request = urllib.request.Request(
        f"{base}/_calls",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 (fixed host)
        return json.loads(response.read())["calls"]

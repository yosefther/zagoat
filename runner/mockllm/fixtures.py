"""Recorded mock-LLM answers per task, loaded from problems/<id>/<mock_llm>.jsonl.

Each line is one of:
    {"kind": "chat", "user": "<last user message>", "response": "<assistant reply>"}
    {"kind": "embedding", "input": "<text>", "vector": [0.1, ...]}

Chat prompts match on the last user message with whitespace collapsed.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class TaskFixtures:
    chat: dict[str, str] = field(default_factory=dict)
    embeddings: dict[str, list[float]] = field(default_factory=dict)


def load_task_fixtures(path: Path) -> TaskFixtures:
    fixtures = TaskFixtures()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if row["kind"] == "chat":
                fixtures.chat[normalize(row["user"])] = str(row["response"])
            elif row["kind"] == "embedding":
                fixtures.embeddings[normalize(row["input"])] = [float(v) for v in row["vector"]]
            else:
                raise ValueError(f"unknown kind {row['kind']!r}")
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f"{path}:{number}: {exc}") from exc
    return fixtures


def load_all_fixtures(problems_dir: Path) -> dict[str, TaskFixtures]:
    """Fixtures for every task that declares `mock_llm` in its problem.yaml."""
    result: dict[str, TaskFixtures] = {}
    for spec_path in sorted(problems_dir.glob("*/problem.yaml")):
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        relative = spec.get("mock_llm")
        if relative:
            result[spec_path.parent.name] = load_task_fixtures(spec_path.parent / relative)
    return result

"""The parts of problem.yaml the runner needs. The API owns the full schema
(api/app/problems/schema.py); this reader only trusts what CI has already validated."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml


@dataclass(frozen=True)
class MetricSpec:
    name: str
    threshold: float
    goal: Literal["at_least", "at_most"] = "at_least"

    def met(self, value: float) -> bool:
        return value >= self.threshold if self.goal == "at_least" else value <= self.threshold


@dataclass(frozen=True)
class TaskSpec:
    id: str
    root: Path
    image: str
    starter_dir: Path
    reference_dir: Path
    data_dir: Path | None
    sample_tests: Path
    hidden_tests: Path
    metrics: tuple[MetricSpec, ...]

    def read_files(self, folder: Path) -> dict[str, str]:
        return {
            p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        }

    def starter_files(self) -> dict[str, str]:
        return self.read_files(self.starter_dir)

    def reference_solution(self) -> dict[str, str]:
        """Starter files with the reference files laid over them."""
        return {**self.starter_files(), **self.read_files(self.reference_dir)}


def load_task(root: Path) -> TaskSpec:
    root = root.resolve()
    raw = yaml.safe_load((root / "problem.yaml").read_text(encoding="utf-8"))
    files = raw.get("files", {})
    grader = raw.get("grader", {})
    data = files.get("data", "data/")
    return TaskSpec(
        id=raw["id"],
        root=root,
        image=raw["image"],
        starter_dir=root / files.get("starter", "starter/"),
        reference_dir=root / files.get("reference", "reference/"),
        data_dir=(root / data) if data else None,
        sample_tests=root / grader.get("sample_tests", "tests/sample/"),
        hidden_tests=root / grader.get("hidden_tests", "tests/hidden/"),
        metrics=tuple(
            MetricSpec(m["name"], float(m["threshold"]), m.get("goal", "at_least"))
            for m in grader.get("metrics", [])
        ),
    )


def load_tasks(problems_dir: Path) -> dict[str, TaskSpec]:
    return {p.parent.name: load_task(p.parent) for p in sorted(problems_dir.glob("*/problem.yaml"))}

"""Read a task folder into the parts the API may store and show.

Hidden tests, graders and mock-LLM fixtures are never read here: they ship only to the
runner (brief, section 5). Sample tests are public.
"""

import hashlib
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.problems.schema import PathSpec, ProblemSpec

# Starter and reference files must be small text files the editor can show.
MAX_CODE_FILE_BYTES = 200_000
# The landing page quotes a short stretch of starter code, not a whole file. Wider lines
# get cut off in its code box at desktop widths.
MAX_PREVIEW_LINES = 15
MAX_PREVIEW_WIDTH = 60
# Ids that would collide with fixed API routes such as GET /problems/featured.
RESERVED_IDS = {"featured"}
CODE_FILE_SUFFIXES = {".py", ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".toml"}


class ProblemError(Exception):
    """A task folder is invalid. The message says which file and what to fix."""


@dataclass(frozen=True)
class PublicProblem:
    spec: ProblemSpec
    content_hash: str
    statement: str
    starter_files: dict[str, str]
    hints: list[str]
    walkthrough: str | None
    reference_files: dict[str, str]
    sample_tests: dict[str, str]
    # The landing-page preview, ready to serve: order, file, code, checks and gauge.
    featured: dict[str, Any] | None = None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ProblemError(f"{path}: must be UTF-8 text") from exc


def _read_code_dir(root: Path, relative: str) -> dict[str, str]:
    folder = root / relative
    if not folder.is_dir():
        raise ProblemError(f"{folder}: folder is missing")
    files: dict[str, str] = {}
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts:
            continue
        name = path.relative_to(folder).as_posix()
        if path.suffix not in CODE_FILE_SUFFIXES:
            raise ProblemError(f"{path}: only text files ({', '.join(sorted(CODE_FILE_SUFFIXES))})")
        if path.stat().st_size > MAX_CODE_FILE_BYTES:
            raise ProblemError(f"{path}: larger than {MAX_CODE_FILE_BYTES} bytes")
        files[name] = _read_text(path)
    if not files:
        raise ProblemError(f"{folder}: folder is empty")
    return files


def split_hints(markdown: str) -> list[str]:
    """Split hints.md into one hint per `## ` heading; text before the first one is ignored."""
    parts = re.split(r"^## .*$", markdown, flags=re.MULTILINE)
    return [part.strip() for part in parts[1:] if part.strip()]


def content_hash(root: Path) -> str:
    """Hash every file in the task folder, so any change (hidden tests too) bumps the version."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def featured_preview(
    spec: ProblemSpec, starter: dict[str, str], spec_path: Path
) -> dict[str, Any] | None:
    """Check the `featured` block against the starter code and grader, and cut the snippet."""
    featured = spec.featured
    if featured is None:
        return None
    if spec.access != "free":
        # Starter code needs access to the task (brief, section 7), so only free tasks qualify.
        raise ProblemError(f"{spec_path}: only free tasks can be featured")
    if len(set(featured.checks)) != len(featured.checks):
        raise ProblemError(f"{spec_path}: featured.checks lists a check twice")
    if featured.file not in starter:
        raise ProblemError(f"{spec_path}: featured.file '{featured.file}' is not a starter file")
    lines = starter[featured.file].splitlines()
    first, last = featured.lines
    if not 1 <= first <= last <= len(lines):
        raise ProblemError(
            f"{spec_path}: featured.lines {first}-{last} is outside {featured.file} "
            f"(1-{len(lines)})"
        )
    if last - first + 1 > MAX_PREVIEW_LINES:
        raise ProblemError(f"{spec_path}: featured.lines shows more than {MAX_PREVIEW_LINES} lines")
    # Dedented, so a stretch from inside a function starts at the left edge.
    code = textwrap.dedent("\n".join(lines[first - 1 : last]))
    widest = max(len(line) for line in code.splitlines())
    if widest > MAX_PREVIEW_WIDTH:
        raise ProblemError(
            f"{spec_path}: featured.lines has a line of {widest} characters once dedented; "
            f"keep them to {MAX_PREVIEW_WIDTH}"
        )
    gauge = None
    if featured.gauge:
        metric = next((m for m in spec.grader.metrics if m.name == featured.gauge.metric), None)
        if metric is None:
            raise ProblemError(
                f"{spec_path}: featured.gauge.metric '{featured.gauge.metric}' "
                "is not a grader metric"
            )
        if metric.goal != "at_least" or not 0 <= metric.threshold <= 1:
            raise ProblemError(
                f"{spec_path}: featured.gauge needs an at_least metric with a threshold from 0 to 1"
            )
        if featured.gauge.starter_value >= metric.threshold:
            raise ProblemError(
                f"{spec_path}: featured.gauge.starter_value must be below the threshold "
                f"({metric.threshold})"
            )
        gauge = {
            "label": featured.gauge.label,
            "threshold": metric.threshold,
            "starter_value": featured.gauge.starter_value,
        }
    return {
        "order": featured.order,
        "file": featured.file,
        "code": code,
        "checks": list(featured.checks),
        "gauge": gauge,
    }


def load_spec(root: Path) -> ProblemSpec:
    spec_path = root / "problem.yaml"
    if not spec_path.is_file():
        raise ProblemError(f"{spec_path}: file is missing")
    try:
        raw = yaml.safe_load(_read_text(spec_path))
        spec = ProblemSpec.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        raise ProblemError(f"{spec_path}: {exc}") from exc
    if spec.id in RESERVED_IDS:
        raise ProblemError(f"{spec_path}: id '{spec.id}' is reserved; pick another")
    if spec.id != root.name:
        raise ProblemError(f"{spec_path}: id '{spec.id}' must match the folder name '{root.name}'")
    return spec


def load_problem(root: Path) -> PublicProblem:
    spec = load_spec(root)
    files = spec.files

    def required(relative: str) -> Path:
        path = root / relative
        if not path.exists():
            raise ProblemError(f"{path}: is missing")
        return path

    def optional_text(relative: str | None) -> str | None:
        return _read_text(required(relative)) if relative else None

    for relative in (spec.grader.sample_tests, spec.grader.hidden_tests):
        if not any(required(relative).glob("test_*.py")):
            raise ProblemError(f"{root / relative}: needs at least one test_*.py file")
    if spec.files.data:
        required(spec.files.data)
    if spec.mock_llm:
        required(spec.mock_llm)

    starter = _read_code_dir(root, files.starter)
    reference = _read_code_dir(root, files.reference)
    unknown = sorted(set(reference) - set(starter))
    if unknown:
        raise ProblemError(
            f"{root / files.reference}: files not in the starter: {', '.join(unknown)}"
        )

    hints_md = optional_text(files.hints)
    hints = split_hints(hints_md) if hints_md else []
    if hints_md is not None and not hints:
        raise ProblemError(f"{root / str(files.hints)}: add hints as '## Hint 1' sections")

    return PublicProblem(
        spec=spec,
        content_hash=content_hash(root),
        statement=_read_text(required(files.statement)),
        starter_files=starter,
        hints=hints,
        walkthrough=optional_text(files.walkthrough),
        reference_files=reference,
        sample_tests=_read_code_dir(root, spec.grader.sample_tests),
        featured=featured_preview(spec, starter, root / "problem.yaml"),
    )


def load_all(problems_dir: Path) -> list[PublicProblem]:
    """Load every task folder (folders starting with '_' or '.' are skipped)."""
    if not problems_dir.is_dir():
        raise ProblemError(f"{problems_dir}: problems folder is missing")
    roots = sorted(
        p for p in problems_dir.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))
    )
    return [load_problem(root) for root in roots]


PATHS_FILE = "paths.yaml"


def load_paths(problems_dir: Path, task_ids: set[str]) -> list[PathSpec]:
    """Read problems/paths.yaml. Every task id must exist; path ids must be unique."""
    path_file = problems_dir / PATHS_FILE
    if not path_file.is_file():
        return []
    try:
        raw = yaml.safe_load(_read_text(path_file)) or []
        if not isinstance(raw, list):
            raise ProblemError(f"{path_file}: must be a list of paths")
        paths = [PathSpec.model_validate(item) for item in raw]
    except (yaml.YAMLError, ValidationError) as exc:
        raise ProblemError(f"{path_file}: {exc}") from exc
    seen: set[str] = set()
    for spec in paths:
        if spec.id in seen:
            raise ProblemError(f"{path_file}: path id '{spec.id}' is used twice")
        seen.add(spec.id)
        missing = [task for task in spec.tasks if task not in task_ids]
        if missing:
            raise ProblemError(
                f"{path_file}: path '{spec.id}' lists unknown tasks: {', '.join(missing)}"
            )
        if len(set(spec.tasks)) != len(spec.tasks):
            raise ProblemError(f"{path_file}: path '{spec.id}' lists a task twice")
    return paths

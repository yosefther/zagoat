"""Read a task folder into the parts the API may store and show.

Hidden tests, graders and mock-LLM fixtures are never read here: they ship only to the
runner (brief, section 5). Sample tests are public.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.problems.schema import ProblemSpec

# Starter and reference files must be small text files the editor can show.
MAX_CODE_FILE_BYTES = 200_000
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


def load_spec(root: Path) -> ProblemSpec:
    spec_path = root / "problem.yaml"
    if not spec_path.is_file():
        raise ProblemError(f"{spec_path}: file is missing")
    try:
        raw = yaml.safe_load(_read_text(spec_path))
        spec = ProblemSpec.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        raise ProblemError(f"{spec_path}: {exc}") from exc
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
    )


def load_all(problems_dir: Path) -> list[PublicProblem]:
    """Load every task folder (folders starting with '_' or '.' are skipped)."""
    if not problems_dir.is_dir():
        raise ProblemError(f"{problems_dir}: problems folder is missing")
    roots = sorted(
        p for p in problems_dir.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))
    )
    return [load_problem(root) for root in roots]

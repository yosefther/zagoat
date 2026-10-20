from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LearningPath, Problem
from app.problems.loader import PublicProblem, load_all, load_paths
from app.problems.schema import PathSpec


@dataclass
class SyncReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    unpublished: list[str] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)


def _apply(row: Problem, problem: PublicProblem) -> None:
    spec = problem.spec
    row.title = spec.title
    row.summary = spec.summary
    row.category = spec.category
    row.difficulty = spec.difficulty
    row.est_minutes = spec.est_minutes
    row.access = spec.access
    row.published = spec.published
    row.content_hash = problem.content_hash
    row.statement = problem.statement
    row.starter_files = problem.starter_files
    row.hints = problem.hints
    row.walkthrough = problem.walkthrough
    row.reference_files = problem.reference_files
    row.sample_tests = problem.sample_tests
    row.metrics = [metric.model_dump() for metric in spec.grader.metrics]


def sync_problems(db: Session, problems: list[PublicProblem]) -> SyncReport:
    """Upsert problems. Content changes bump the version; missing problems are unpublished.

    Rows are never deleted, because submissions keep pointing at them.
    """
    report = SyncReport()
    existing = {row.id: row for row in db.scalars(select(Problem))}
    for problem in problems:
        row = existing.pop(problem.spec.id, None)
        if row is None:
            row = Problem(id=problem.spec.id, version=1)
            _apply(row, problem)
            db.add(row)
            report.created.append(row.id)
        else:
            changed = (
                row.content_hash != problem.content_hash or row.published != problem.spec.published
            )
            if row.content_hash != problem.content_hash:
                row.version += 1
            # Always refresh the stored fields, so columns added later get filled in.
            _apply(row, problem)
            (report.updated if changed else report.unchanged).append(row.id)
    for row in existing.values():
        if row.published:
            row.published = False
            report.unpublished.append(row.id)
    db.commit()
    return report


def sync_paths(db: Session, paths: list[PathSpec], report: SyncReport) -> None:
    """Replace all paths with the file's contents, keeping the file's order."""
    existing = {row.id: row for row in db.scalars(select(LearningPath))}
    for position, spec in enumerate(paths):
        row = existing.pop(spec.id, None) or LearningPath(id=spec.id)
        row.title = spec.title
        row.summary = spec.summary
        row.position = position
        row.task_ids = list(spec.tasks)
        db.add(row)
        report.paths.append(spec.id)
    for row in existing.values():
        db.delete(row)
    db.commit()


def sync_from_dir(db: Session, problems_dir: Path) -> SyncReport:
    problems = load_all(problems_dir)
    # Validate paths before writing anything, so a bad paths.yaml changes nothing.
    paths = load_paths(problems_dir, {p.spec.id for p in problems})
    report = sync_problems(db, problems)
    sync_paths(db, paths, report)
    return report

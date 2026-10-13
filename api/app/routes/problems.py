from typing import Any, Literal

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import DbSession
from app.entitlements import LockReason, has_paid_access, solve_lock
from app.errors import AppError
from app.models import Problem
from app.security.sessions import OptionalAuth

router = APIRouter(prefix="/problems")

CATEGORY_ORDER = {"rag": 0, "training": 1, "evals": 2, "serving": 3}
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


class ProblemSummary(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    difficulty: str
    est_minutes: int
    access: Literal["free", "paid"]
    progress: str | None = None


class ProblemDetail(ProblemSummary):
    version: int
    statement: str
    metrics: list[dict[str, Any]]
    hint_count: int
    has_walkthrough: bool
    # Signed-in users with access only.
    lock: LockReason | None
    starter_files: dict[str, str] | None


def summary_of(problem: Problem) -> ProblemSummary:
    return ProblemSummary(
        id=problem.id,
        title=problem.title,
        summary=problem.summary,
        category=problem.category,
        difficulty=problem.difficulty,
        est_minutes=problem.est_minutes,
        access=problem.access,
    )


def get_published(db: Session, problem_id: str) -> Problem:
    problem = db.get(Problem, problem_id)
    if problem is None or not problem.published:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "problem_not_found",
            "We couldn't find that problem. It may have been renamed or removed.",
        )
    return problem


@router.get("", response_model=list[ProblemSummary])
def list_problems(db: DbSession, auth: OptionalAuth) -> list[ProblemSummary]:
    problems = db.scalars(select(Problem).where(Problem.published.is_(True))).all()
    ordered = sorted(
        problems,
        key=lambda p: (CATEGORY_ORDER.get(p.category, 9), DIFFICULTY_ORDER[p.difficulty], p.title),
    )
    return [summary_of(p) for p in ordered]


@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(problem_id: str, db: DbSession, auth: OptionalAuth) -> ProblemDetail:
    problem = get_published(db, problem_id)
    user = auth.user if auth else None
    lock = solve_lock(problem, user, has_paid_access(db, user))
    return ProblemDetail(
        **summary_of(problem).model_dump(),
        version=problem.version,
        statement=problem.statement,
        metrics=problem.metrics,
        hint_count=len(problem.hints),
        has_walkthrough=problem.walkthrough is not None,
        lock=lock,
        starter_files=problem.starter_files if lock is None else None,
    )

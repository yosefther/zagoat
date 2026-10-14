from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.code_files import validate_files
from app.config import Settings, get_settings
from app.db import DbSession
from app.entitlements import LockReason, has_paid_access, solve_lock
from app.errors import AppError
from app.models import Draft, Problem
from app.security.csrf import require_csrf
from app.security.sessions import OptionalAuth, RequiredAuth

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
    draft_files: dict[str, str] | None
    draft_updated_at: datetime | None


class DraftRequest(BaseModel):
    files: dict[str, str]


class DraftResponse(BaseModel):
    updated_at: datetime


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
    draft = db.get(Draft, (user.id, problem.id)) if user and lock is None else None
    return ProblemDetail(
        **summary_of(problem).model_dump(),
        version=problem.version,
        statement=problem.statement,
        metrics=problem.metrics,
        hint_count=len(problem.hints),
        has_walkthrough=problem.walkthrough is not None,
        lock=lock,
        starter_files=problem.starter_files if lock is None else None,
        draft_files=draft.files if draft else None,
        draft_updated_at=draft.updated_at if draft else None,
    )


def require_solvable(db: Session, problem: Problem, auth: RequiredAuth) -> None:
    lock = solve_lock(problem, auth.user, has_paid_access(db, auth.user))
    if lock == "paid":
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "paid_problem",
            "This problem is part of Lifetime and Pro. Upgrade to edit and submit it.",
        )


@router.put(
    "/{problem_id}/draft", response_model=DraftResponse, dependencies=[Depends(require_csrf)]
)
def save_draft(
    problem_id: str,
    body: DraftRequest,
    db: DbSession,
    auth: RequiredAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> DraftResponse:
    problem = get_published(db, problem_id)
    require_solvable(db, problem, auth)
    files = validate_files(body.files, problem, settings)
    draft = db.get(Draft, (auth.user.id, problem.id))
    if draft is None:
        draft = Draft(user_id=auth.user.id, problem_id=problem.id, files=files)
        db.add(draft)
    else:
        draft.files = files
    db.commit()
    db.refresh(draft)
    return DraftResponse(updated_at=draft.updated_at)

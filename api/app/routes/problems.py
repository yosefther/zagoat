from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.code_files import validate_files
from app.config import Settings, get_settings
from app.db import DbSession
from app.entitlements import LockReason, require_paid, require_solvable, solve_lock
from app.errors import AppError
from app.models import Draft, Problem, Progress, Submission
from app.plans import plan_for
from app.progress import get_or_create, get_progress, mark_started, reference_unlocked
from app.redis_client import RedisClient
from app.security.csrf import require_csrf
from app.security.sessions import OptionalAuth, RequiredAuth
from app.usage import usage_for

router = APIRouter(prefix="/problems")

CATEGORY_ORDER = {"rag": 0, "training": 1, "evals": 2, "serving": 3}
DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}

SettingsDep = Annotated[Settings, Depends(get_settings)]


class ProblemSummary(BaseModel):
    id: str
    title: str
    summary: str
    category: str
    difficulty: str
    est_minutes: int
    access: Literal["free", "paid"]
    progress: str | None = None
    best_result: "BestResult | None" = None


class BestResult(BaseModel):
    """The user's best Submit: the first metric's best value, else the most tests passed."""

    value: float  # for sorting: the metric value, or the share of tests passed
    label: str  # for display, e.g. "0.96" or "16/16 tests"


class ProgressOut(BaseModel):
    state: str
    hints_revealed: int
    first_submit_at: datetime | None
    solved_at: datetime | None
    timer_seconds: int | None


class UsageOut(BaseModel):
    submits_used: int
    submits_limit: int
    submits_reset_at: datetime
    runs_used: int
    runs_limit: int
    runs_reset_at: datetime


class ProblemDetail(ProblemSummary):
    version: int
    statement: str
    sample_tests: dict[str, str]
    metrics: list[dict[str, Any]]
    hint_count: int
    has_walkthrough: bool
    # Everything below depends on who is asking; visitors get empty values.
    lock: LockReason | None
    read_only: bool
    starter_files: dict[str, str] | None
    draft_files: dict[str, str] | None
    draft_updated_at: datetime | None
    hints: list[str]
    progress_detail: ProgressOut | None
    reference_unlocked: bool
    walkthrough_unlocked: bool
    plan: str | None
    usage: UsageOut | None


class GaugeOut(BaseModel):
    label: str
    threshold: float
    starter_value: float


class FeaturedTask(BaseModel):
    """A read-only landing-page preview. Public data only: starter code, never hidden tests."""

    id: str
    title: str
    summary: str
    category: str
    difficulty: str
    est_minutes: int
    access: Literal["free", "paid"]
    file: str
    code: str
    checks: list[str]
    gauge: GaugeOut | None


class DraftRequest(BaseModel):
    files: dict[str, str]


class DraftResponse(BaseModel):
    updated_at: datetime


class HintResponse(BaseModel):
    number: int
    hint: str
    hints_revealed: int


class MarkdownResponse(BaseModel):
    markdown: str


class FilesResponse(BaseModel):
    files: dict[str, str]


class HistoryItem(BaseModel):
    job_id: str
    problem_id: str
    problem_version: int
    kind: Literal["run", "submit"]
    status: str
    verdict: str | None
    tests_passed: int | None
    tests_total: int | None
    metrics: list[dict[str, Any]]
    duration_ms: int | None
    timer_seconds: int | None
    created_at: datetime


def summary_of(problem: Problem, progress: Progress | None = None) -> ProblemSummary:
    return ProblemSummary(
        id=problem.id,
        title=problem.title,
        summary=problem.summary,
        category=problem.category,
        difficulty=problem.difficulty,
        est_minutes=problem.est_minutes,
        access=problem.access,
        progress=progress.state if progress else None,
    )


def history_item(submission: Submission) -> HistoryItem:
    return HistoryItem(
        job_id=submission.id.hex,
        problem_id=submission.problem_id,
        problem_version=submission.problem_version,
        kind=submission.kind,
        status=submission.status,
        verdict=submission.verdict,
        tests_passed=submission.tests_passed,
        tests_total=submission.tests_total,
        metrics=submission.metrics or [],
        duration_ms=submission.duration_ms,
        timer_seconds=submission.timer_seconds,
        created_at=submission.created_at,
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


def best_results(db: Session, user_id: Any, problems: dict[str, Problem]) -> dict[str, BestResult]:
    """Best graded Submit per problem. system_error Submits don't count."""
    rows = db.scalars(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.kind == "submit",
            Submission.status == "done",
            Submission.verdict != "system_error",
        )
    ).all()
    best: dict[str, BestResult] = {}
    for row in rows:
        problem = problems.get(row.problem_id)
        if problem is None:
            continue
        result = _result_of(row, problem)
        if result is None:
            continue
        current = best.get(row.problem_id)
        lower_is_better = bool(problem.metrics) and problem.metrics[0].get("goal") == "at_most"
        if current is None or (
            result.value < current.value if lower_is_better else result.value > current.value
        ):
            best[row.problem_id] = result
    return best


def _result_of(row: Submission, problem: Problem) -> BestResult | None:
    if problem.metrics:
        name = problem.metrics[0]["name"]
        value = next((m.get("value") for m in row.metrics or [] if m.get("name") == name), None)
        return None if value is None else BestResult(value=value, label=f"{value:.2f}")
    if row.tests_total:
        passed = row.tests_passed or 0
        return BestResult(value=passed / row.tests_total, label=f"{passed}/{row.tests_total} tests")
    return None


@router.get("", response_model=list[ProblemSummary])
def list_problems(db: DbSession, auth: OptionalAuth) -> list[ProblemSummary]:
    problems = db.scalars(select(Problem).where(Problem.published.is_(True))).all()
    progress: dict[str, Progress] = {}
    best: dict[str, BestResult] = {}
    if auth:
        rows = db.scalars(select(Progress).where(Progress.user_id == auth.user.id)).all()
        progress = {row.problem_id: row for row in rows}
        best = best_results(db, auth.user.id, {p.id: p for p in problems})
    ordered = sorted(
        problems,
        key=lambda p: (CATEGORY_ORDER.get(p.category, 9), DIFFICULTY_ORDER[p.difficulty], p.title),
    )
    return [
        summary_of(p, progress.get(p.id)).model_copy(update={"best_result": best.get(p.id)})
        for p in ordered
    ]


@router.get("/featured", response_model=list[FeaturedTask])
def list_featured(db: DbSession) -> list[FeaturedTask]:
    """Free tasks whose problem.yaml has a `featured` block, in their chosen order.

    The loader already rejects featured paid tasks; filtering here too means paid starter code
    can't reach visitors even if a row slips through.
    """
    problems = db.scalars(
        select(Problem).where(
            Problem.published.is_(True),
            Problem.access == "free",
            Problem.featured.is_not(None),
        )
    ).all()
    previews = sorted(
        ((p, p.featured) for p in problems if p.featured),
        key=lambda pair: (pair[1]["order"], pair[0].id),
    )
    return [
        FeaturedTask(
            id=p.id,
            title=p.title,
            summary=p.summary,
            category=p.category,
            difficulty=p.difficulty,
            est_minutes=p.est_minutes,
            access=p.access,
            file=preview["file"],
            code=preview["code"],
            checks=preview["checks"],
            gauge=preview["gauge"],
        )
        for p, preview in previews
    ]


@router.get("/{problem_id}", response_model=ProblemDetail)
def get_problem(
    problem_id: str, db: DbSession, redis: RedisClient, auth: OptionalAuth, settings: SettingsDep
) -> ProblemDetail:
    problem = get_published(db, problem_id)
    user = auth.user if auth else None
    plan = plan_for(db, user, settings)
    lock = solve_lock(problem, user, plan)
    progress = get_progress(db, user.id, problem.id) if user else None
    draft = db.get(Draft, (user.id, problem.id)) if user else None
    # After a downgrade, a paid problem the user worked on stays readable (section 11).
    read_only = lock == "paid" and (draft is not None or progress is not None)
    show_code = lock is None or read_only
    usage = usage_for(db, redis, user, plan) if user else None
    hints_revealed = progress.hints_revealed if progress and lock is None else 0
    return ProblemDetail(
        **summary_of(problem, progress).model_dump(),
        version=problem.version,
        statement=problem.statement,
        sample_tests=problem.sample_tests,
        metrics=problem.metrics,
        hint_count=len(problem.hints),
        has_walkthrough=problem.walkthrough is not None,
        lock=lock,
        read_only=read_only,
        starter_files=problem.starter_files if show_code else None,
        draft_files=draft.files if draft and show_code else None,
        draft_updated_at=draft.updated_at if draft and show_code else None,
        hints=problem.hints[:hints_revealed],
        progress_detail=ProgressOut.model_validate(progress, from_attributes=True)
        if progress
        else None,
        reference_unlocked=reference_unlocked(progress),
        walkthrough_unlocked=plan.paid and problem.walkthrough is not None,
        plan=plan.name if user else None,
        usage=UsageOut.model_validate(usage, from_attributes=True) if usage else None,
    )


@router.put(
    "/{problem_id}/draft", response_model=DraftResponse, dependencies=[Depends(require_csrf)]
)
def save_draft(
    problem_id: str, body: DraftRequest, db: DbSession, auth: RequiredAuth, settings: SettingsDep
) -> DraftResponse:
    problem = get_published(db, problem_id)
    require_solvable(problem, auth.user, plan_for(db, auth.user, settings))
    files = validate_files(body.files, problem, settings)
    draft = db.get(Draft, (auth.user.id, problem.id))
    if draft is None:
        draft = Draft(user_id=auth.user.id, problem_id=problem.id, files=files)
        db.add(draft)
    else:
        draft.files = files
    mark_started(db, auth.user.id, problem.id)
    db.commit()
    db.refresh(draft)
    return DraftResponse(updated_at=draft.updated_at)


@router.post(
    "/{problem_id}/hints/{number}",
    response_model=HintResponse,
    dependencies=[Depends(require_csrf)],
)
def reveal_hint(
    problem_id: str,
    number: Annotated[int, Path(ge=1)],
    db: DbSession,
    auth: RequiredAuth,
    settings: SettingsDep,
) -> HintResponse:
    """Reveal hints one at a time. Re-reading a revealed hint is fine; skipping ahead isn't."""
    problem = get_published(db, problem_id)
    require_solvable(problem, auth.user, plan_for(db, auth.user, settings))
    if number > len(problem.hints):
        raise AppError(
            status.HTTP_404_NOT_FOUND, "hint_not_found", "This problem has no more hints."
        )
    progress = get_or_create(db, auth.user.id, problem.id)
    if number > progress.hints_revealed + 1:
        raise AppError(
            status.HTTP_409_CONFLICT,
            "hint_out_of_order",
            f"Reveal hint {progress.hints_revealed + 1} first.",
        )
    progress.hints_revealed = max(progress.hints_revealed, number)
    db.commit()
    return HintResponse(
        number=number, hint=problem.hints[number - 1], hints_revealed=progress.hints_revealed
    )


@router.get("/{problem_id}/walkthrough", response_model=MarkdownResponse)
def get_walkthrough(
    problem_id: str, db: DbSession, auth: RequiredAuth, settings: SettingsDep
) -> MarkdownResponse:
    problem = get_published(db, problem_id)
    require_paid(plan_for(db, auth.user, settings))
    if problem.walkthrough is None:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "walkthrough_not_found",
            "This problem doesn't have a walkthrough yet.",
        )
    return MarkdownResponse(markdown=problem.walkthrough)


@router.get("/{problem_id}/reference", response_model=FilesResponse)
def get_reference(problem_id: str, db: DbSession, auth: RequiredAuth) -> FilesResponse:
    problem = get_published(db, problem_id)
    if not reference_unlocked(get_progress(db, auth.user.id, problem.id)):
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "reference_locked",
            "The reference solution unlocks after your first Submit on this problem.",
        )
    return FilesResponse(files=problem.reference_files)


@router.get("/{problem_id}/submissions", response_model=list[HistoryItem])
def problem_history(
    problem_id: str, db: DbSession, auth: RequiredAuth, kind: Literal["run", "submit"] = "submit"
) -> list[HistoryItem]:
    problem = get_published(db, problem_id)
    rows = db.scalars(
        select(Submission)
        .where(
            Submission.user_id == auth.user.id,
            Submission.problem_id == problem.id,
            Submission.kind == kind,
        )
        .order_by(Submission.created_at.desc())
        .limit(100)
    ).all()
    return [history_item(row) for row in rows]

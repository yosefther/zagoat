import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.clock import utcnow
from app.code_files import validate_files
from app.config import Settings, get_settings
from app.db import DbSession
from app.errors import AppError
from app.jobs import enqueue, expire_if_stale, is_open
from app.models import Submission, User
from app.redis_client import RedisClient
from app.routes.problems import get_published, require_solvable
from app.security.csrf import require_csrf
from app.security.internal import require_worker
from app.security.sessions import RequiredAuth

router = APIRouter()

Kind = Literal["run", "submit"]
Verdict = Literal["passed", "failed", "error", "time_limit", "memory_limit", "system_error"]


class JobRequest(BaseModel):
    files: dict[str, str]


class JobCreated(BaseModel):
    job_id: str


class JobResponse(BaseModel):
    job_id: str
    problem_id: str
    problem_version: int
    kind: Kind
    status: Literal["queued", "running", "done"]
    verdict: Verdict | None
    message: str | None
    tests_passed: int | None
    tests_total: int | None
    tests: list[dict[str, Any]]
    metrics: list[dict[str, Any]]
    stdout: str | None
    stderr: str | None
    duration_ms: int | None
    created_at: datetime


def job_response(submission: Submission) -> JobResponse:
    results = submission.results or {}
    return JobResponse(
        job_id=submission.id.hex,
        problem_id=submission.problem_id,
        problem_version=submission.problem_version,
        kind=submission.kind,
        status=submission.status,
        verdict=submission.verdict,
        message=results.get("message"),
        tests_passed=submission.tests_passed,
        tests_total=submission.tests_total,
        tests=results.get("tests", []),
        metrics=submission.metrics or [],
        stdout=results.get("stdout"),
        stderr=results.get("stderr"),
        duration_ms=submission.duration_ms,
        created_at=submission.created_at,
    )


def _parse_job_id(job_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(hex=job_id)
    except ValueError as exc:
        raise AppError(
            status.HTTP_404_NOT_FOUND, "job_not_found", "We couldn't find that job."
        ) from exc


def create_job(
    kind: Kind,
    problem_id: str,
    body: JobRequest,
    db: DbSession,
    redis: RedisClient,
    auth: RequiredAuth,
    settings: Settings,
) -> JobCreated:
    problem = get_published(db, problem_id)
    require_solvable(db, problem, auth)
    files = validate_files(body.files, problem, settings)

    # Lock the user's row so two clicks at once can't both pass the one-job-at-a-time check.
    db.execute(select(User.id).where(User.id == auth.user.id).with_for_update())
    open_jobs = db.scalars(
        select(Submission).where(
            Submission.user_id == auth.user.id, Submission.status.in_(("queued", "running"))
        )
    ).all()
    for job in open_jobs:
        expire_if_stale(db, job, settings)
    if any(is_open(job) for job in open_jobs):
        raise AppError(
            status.HTTP_409_CONFLICT,
            "job_in_progress",
            "You already have a run or submission in progress. Wait for it to finish.",
        )

    submission = Submission(
        user_id=auth.user.id,
        problem_id=problem.id,
        problem_version=problem.version,
        kind=kind,
        files=files,
        status="queued",
        created_at=utcnow(),
    )
    db.add(submission)
    db.flush()
    enqueue(redis, settings, submission)
    db.commit()
    return JobCreated(job_id=submission.id.hex)


@router.post(
    "/problems/{problem_id}/runs",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_csrf)],
)
def create_run(
    problem_id: str,
    body: JobRequest,
    db: DbSession,
    redis: RedisClient,
    auth: RequiredAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobCreated:
    return create_job("run", problem_id, body, db, redis, auth, settings)


@router.post(
    "/problems/{problem_id}/submissions",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(require_csrf)],
)
def create_submission(
    problem_id: str,
    body: JobRequest,
    db: DbSession,
    redis: RedisClient,
    auth: RequiredAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobCreated:
    return create_job("submit", problem_id, body, db, redis, auth, settings)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: DbSession,
    auth: RequiredAuth,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobResponse:
    submission = db.get(Submission, _parse_job_id(job_id))
    if submission is None or submission.user_id != auth.user.id:
        raise AppError(status.HTTP_404_NOT_FOUND, "job_not_found", "We couldn't find that job.")
    if expire_if_stale(db, submission, settings):
        db.commit()
    return job_response(submission)


class WorkerResult(BaseModel):
    verdict: Verdict
    message: str | None = None
    tests_passed: int = 0
    tests_total: int = 0
    tests: list[dict[str, Any]] = Field(default_factory=list)
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    stdout: str | None = None
    stderr: str | None = None
    duration_ms: int = 0


internal = APIRouter(prefix="/internal", dependencies=[Depends(require_worker)])


@internal.post("/jobs/{job_id}/started", status_code=204)
def job_started(job_id: str, db: DbSession) -> None:
    submission = db.get(Submission, _parse_job_id(job_id))
    if submission is not None and submission.status == "queued":
        submission.status = "running"
        db.commit()


@internal.post("/jobs/{job_id}/result", status_code=204)
def job_result(job_id: str, body: WorkerResult, db: DbSession) -> None:
    submission = db.get(Submission, _parse_job_id(job_id), with_for_update=True)
    if submission is None or submission.status == "done":
        return  # Unknown or already closed (for example expired): nothing to do.
    submission.status = "done"
    submission.verdict = body.verdict
    submission.tests_passed = body.tests_passed
    submission.tests_total = body.tests_total
    submission.metrics = body.metrics
    submission.duration_ms = body.duration_ms
    results: dict[str, Any] = {"message": body.message, "tests": body.tests}
    if submission.kind == "run":
        results |= {"stdout": body.stdout, "stderr": body.stderr}
    submission.results = results
    submission.finished_at = utcnow()
    db.commit()

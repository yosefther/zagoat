"""Queueing Runs and Submits for the runner, and reading their state back."""

import json
from datetime import timedelta

from redis import Redis
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.config import Settings
from app.models import Submission
from app.usage import refund_submit

QUEUE_TIMEOUT_MESSAGE = "Something went wrong on our side. This attempt doesn't count. Try again."


def enqueue(redis: Redis, settings: Settings, submission: Submission) -> None:
    """Push the job as JSON. The runner never unpickles anything from Redis."""
    message = {
        "job_id": submission.id.hex,
        "problem_id": submission.problem_id,
        "problem_version": submission.problem_version,
        "kind": submission.kind,
        "files": submission.files,
        "enqueued_at": submission.created_at.timestamp(),
    }
    redis.lpush(settings.queue_key, json.dumps(message))


def is_open(submission: Submission) -> bool:
    return submission.status in ("queued", "running")


def is_stale(submission: Submission, settings: Settings) -> bool:
    """A job the runner will never finish: it sat in the queue or ran far too long."""
    age = utcnow() - submission.created_at
    if submission.status == "queued":
        limit = settings.queue_timeout_seconds + settings.queue_timeout_grace_seconds
        return age > timedelta(seconds=limit)
    if submission.status == "running":
        return age > timedelta(seconds=settings.job_run_timeout_seconds)
    return False


def expire_if_stale(db: Session, submission: Submission, settings: Settings) -> bool:
    """Close a lost job as system_error and refund it (brief, section 9). True if it did."""
    if not is_open(submission) or not is_stale(submission, settings):
        return False
    refund_submit(db, submission)
    submission.status = "done"
    submission.verdict = "system_error"
    submission.results = {"message": QUEUE_TIMEOUT_MESSAGE, "tests": []}
    submission.metrics = []
    submission.tests_passed = 0
    submission.tests_total = 0
    submission.finished_at = utcnow()
    return True

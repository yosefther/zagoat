"""Progress states and unlocks (brief, section 11). States only move forward."""

import uuid

from sqlalchemy.orm import Session

from app.clock import utcnow
from app.models import Progress, Submission

ORDER = {"not_started": 0, "in_progress": 1, "attempted": 2, "solved": 3}


def get_progress(db: Session, user_id: uuid.UUID, problem_id: str) -> Progress | None:
    return db.get(Progress, (user_id, problem_id))


def get_or_create(db: Session, user_id: uuid.UUID, problem_id: str) -> Progress:
    row = get_progress(db, user_id, problem_id)
    if row is None:
        row = Progress(
            user_id=user_id, problem_id=problem_id, state="not_started", hints_revealed=0
        )
        db.add(row)
        db.flush()
    return row


def advance(row: Progress, state: str) -> None:
    if ORDER[state] > ORDER[row.state]:
        row.state = state


def mark_started(db: Session, user_id: uuid.UUID, problem_id: str) -> None:
    """First draft save or Run."""
    advance(get_or_create(db, user_id, problem_id), "in_progress")


def record_result(db: Session, submission: Submission) -> None:
    """Update progress when a job finishes. Only Submits that didn't hit system_error count."""
    if submission.kind != "submit" or submission.verdict == "system_error":
        return
    row = get_or_create(db, submission.user_id, submission.problem_id)
    now = utcnow()
    if row.first_submit_at is None:
        row.first_submit_at = now
    advance(row, "attempted")
    if submission.timer_seconds is not None:
        row.timer_seconds = submission.timer_seconds
    if submission.verdict == "passed":
        advance(row, "solved")
        row.solved_at = row.solved_at or now


def reference_unlocked(row: Progress | None) -> bool:
    """After the first Submit with any verdict except system_error."""
    return row is not None and row.first_submit_at is not None

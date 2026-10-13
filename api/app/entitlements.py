"""Who may do what (brief, section 8). The browser only hides buttons; these rules decide."""

from typing import Literal

from sqlalchemy.orm import Session

from app.models import Problem, User

LockReason = Literal["sign_in", "paid"]


def has_paid_access(db: Session, user: User | None) -> bool:
    """Lifetime or an active Pro subscription. Billing (Milestone 8) fills this in."""
    return False


def solve_lock(problem: Problem, user: User | None, paid: bool) -> LockReason | None:
    """Why the user can't open the editor, Run or Submit on this problem, or None if they can."""
    if user is None:
        return "sign_in"
    if problem.access == "paid" and not paid:
        return "paid"
    return None

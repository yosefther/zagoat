"""Who may do what (brief, section 8). The browser only hides buttons; these rules decide."""

from typing import Literal

from fastapi import status

from app.errors import AppError
from app.models import Problem, User
from app.plans import Plan

LockReason = Literal["sign_in", "paid"]


def solve_lock(problem: Problem, user: User | None, plan: Plan) -> LockReason | None:
    """Why the user can't use the editor, Run, Submit or hints here, or None if they can."""
    if user is None:
        return "sign_in"
    if problem.access == "paid" and not plan.paid:
        return "paid"
    return None


def require_solvable(problem: Problem, user: User, plan: Plan) -> None:
    if solve_lock(problem, user, plan) == "paid":
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "paid_problem",
            "This problem is part of Lifetime and Pro. Upgrade to edit and submit it.",
        )


def require_paid(plan: Plan) -> None:
    if not plan.paid:
        raise AppError(
            status.HTTP_403_FORBIDDEN,
            "paid_feature",
            "Walkthroughs are part of Lifetime and Pro. Upgrade to read them.",
        )

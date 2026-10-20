from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import DbSession
from app.errors import AppError
from app.models import LearningPath, Problem, Progress
from app.routes.problems import ProblemSummary, best_results, summary_of
from app.security.sessions import Auth, OptionalAuth

router = APIRouter(prefix="/paths")


class PathOut(BaseModel):
    id: str
    title: str
    summary: str
    tasks: list[ProblemSummary]
    solved: int
    next_task_id: str | None


def build_paths(db: Session, auth: Auth | None, rows: list[LearningPath]) -> list[PathOut]:
    problems = {
        p.id: p for p in db.scalars(select(Problem).where(Problem.published.is_(True))).all()
    }
    progress: dict[str, Progress] = {}
    best = {}
    if auth:
        progress = {
            row.problem_id: row
            for row in db.scalars(select(Progress).where(Progress.user_id == auth.user.id))
        }
        best = best_results(db, auth.user.id, problems)
    result = []
    for row in rows:
        # Unpublished tasks drop out of a path instead of breaking it.
        tasks = [
            summary_of(problems[task_id], progress.get(task_id)).model_copy(
                update={"best_result": best.get(task_id)}
            )
            for task_id in row.task_ids
            if task_id in problems
        ]
        if not tasks:
            continue
        solved = sum(1 for task in tasks if task.progress == "solved")
        next_task = next((task.id for task in tasks if task.progress != "solved"), None)
        result.append(
            PathOut(
                id=row.id,
                title=row.title,
                summary=row.summary,
                tasks=tasks,
                solved=solved,
                next_task_id=next_task,
            )
        )
    return result


@router.get("", response_model=list[PathOut])
def list_paths(db: DbSession, auth: OptionalAuth) -> list[PathOut]:
    rows = list(db.scalars(select(LearningPath).order_by(LearningPath.position)))
    return build_paths(db, auth, rows)


@router.get("/{path_id}", response_model=PathOut)
def get_path(path_id: str, db: DbSession, auth: OptionalAuth) -> PathOut:
    row = db.get(LearningPath, path_id)
    paths = build_paths(db, auth, [row]) if row else []
    if not paths:
        raise AppError(
            status.HTTP_404_NOT_FOUND,
            "path_not_found",
            "We couldn't find that path. Pick one from the tasks page.",
        )
    return paths[0]

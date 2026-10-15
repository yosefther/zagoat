"""The job message the API puts on the Redis queue, as JSON (never pickle).

{"job_id": "...", "problem_id": "...", "problem_version": 3, "kind": "run",
 "files": {"main.py": "..."}, "enqueued_at": 1730000000.0}
"""

from typing import Literal

from pydantic import BaseModel, Field


class QueuedJob(BaseModel):
    job_id: str = Field(pattern=r"^[0-9a-f]{32}$")
    problem_id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    problem_version: int
    kind: Literal["run", "submit"]
    files: dict[str, str]
    enqueued_at: float

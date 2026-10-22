"""The problem.yaml schema (brief, section 5). CI rejects any task that doesn't match it."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

SLUG = r"^[a-z0-9]+(-[a-z0-9]+)*$"

Category = Literal["rag", "training", "evals", "serving"]
Difficulty = Literal["easy", "medium", "hard"]
Access = Literal["free", "paid"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TaskFiles(Strict):
    statement: str = "statement.md"
    starter: str = "starter/"
    data: str | None = "data/"
    hints: str | None = "hints.md"
    walkthrough: str | None = "walkthrough.md"
    reference: str = "reference/"


class Metric(Strict):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    threshold: float
    # Most metrics must reach the threshold; latency-style metrics must stay under it.
    goal: Literal["at_least", "at_most"] = "at_least"


class Grader(Strict):
    sample_tests: str = "tests/sample/"
    hidden_tests: str = "tests/hidden/"
    metrics: list[Metric] = []


class Gauge(Strict):
    """The landing page's metric bar: the threshold against where the starter code lands."""

    metric: str  # a grader metric with goal at_least and a threshold between 0 and 1
    label: str = Field(min_length=1, max_length=24)  # e.g. "recall@5"
    starter_value: float = Field(ge=0, le=1)


class Featured(Strict):
    """A read-only preview of the task on the landing page. Leave it out to not feature it."""

    order: int = Field(ge=1)  # lower comes first
    file: str  # a starter file to quote
    lines: tuple[int, int]  # first and last line of that file to show, 1-based
    # Plain-words names of a few hidden tests; results show test names anyway.
    checks: list[Annotated[str, Field(min_length=3, max_length=80)]] = Field(
        min_length=1, max_length=6
    )
    gauge: Gauge | None = None


class ProblemSpec(Strict):
    id: str = Field(pattern=SLUG, max_length=64)
    title: str = Field(min_length=3, max_length=120)
    summary: str = Field(min_length=10, max_length=240)
    category: Category
    difficulty: Difficulty
    est_minutes: int = Field(ge=5, le=180)
    access: Access
    published: bool = True
    image: str = Field(min_length=1)
    files: TaskFiles = TaskFiles()
    grader: Grader = Grader()
    mock_llm: str | None = None
    featured: Featured | None = None


class PathSpec(Strict):
    """One entry in problems/paths.yaml: an ordered route through tasks."""

    id: str = Field(pattern=SLUG, max_length=64)
    title: str = Field(min_length=3, max_length=80)
    summary: str = Field(min_length=10, max_length=200)
    tasks: list[str] = Field(min_length=1)

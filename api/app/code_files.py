"""Validation for the code files a user sends (drafts, Runs and Submits)."""

from fastapi import status

from app.config import Settings
from app.errors import AppError
from app.models import Problem


def validate_files(files: dict[str, str], problem: Problem, settings: Settings) -> dict[str, str]:
    """Accept only the problem's starter file names, within the size cap.

    Missing files fall back to the starter version, so the runner always gets a full set.
    """
    unknown = sorted(set(files) - set(problem.starter_files))
    if unknown:
        raise AppError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "unknown_files",
            f"These files aren't part of this problem: {', '.join(unknown)}. "
            "Reload the page to get the current file list.",
        )
    size = sum(len(content.encode()) for content in files.values())
    if size > settings.max_code_bytes:
        raise AppError(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "code_too_large",
            f"Your code is {size // 1000} KB; the limit is {settings.max_code_bytes // 1000} KB. "
            "Remove large pasted data and try again.",
        )
    return {**problem.starter_files, **files}

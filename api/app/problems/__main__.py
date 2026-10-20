"""Problem tooling.

uv run python -m app.problems validate [PROBLEMS_DIR]   check every task folder
uv run python -m app.problems sync [PROBLEMS_DIR]       copy public parts to Postgres
"""

import argparse
import sys
from pathlib import Path

from app.config import get_settings
from app.db import get_sessionmaker
from app.problems.loader import ProblemError, load_all, load_paths
from app.problems.sync import sync_from_dir

DEFAULT_DIR = Path(__file__).resolve().parents[3] / "problems"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.problems")
    parser.add_argument("command", choices=["validate", "sync"])
    parser.add_argument("problems_dir", nargs="?", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            problems = load_all(args.problems_dir)
            for problem in problems:
                print(f"ok  {problem.spec.id}")
            paths = load_paths(args.problems_dir, {p.spec.id for p in problems})
            print(f"{len(problems)} problem(s) and {len(paths)} path(s) valid")
            return 0
        with get_sessionmaker(get_settings())() as db:
            report = sync_from_dir(db, args.problems_dir)
    except ProblemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for label in ("created", "updated", "unchanged", "unpublished", "paths"):
        names = getattr(report, label)
        print(f"{label}: {', '.join(names) if names else '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

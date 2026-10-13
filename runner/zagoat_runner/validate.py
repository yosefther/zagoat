"""CI task validation (brief, section 5).

    uv run python -m zagoat_runner.validate [PROBLEMS_DIR]

For every task: the reference solution must pass its hidden tests within the Submit time
limit and pass the sample tests; the untouched starter must not pass the hidden tests; and
starter code that raises must get the "error" verdict. Exit code 1 on any failure.
"""

import secrets
import sys
from pathlib import Path

from mockllm.server import background_mock_llm
from zagoat_runner.config import Settings, get_settings
from zagoat_runner.executor import Executor, Job, LocalExecutor
from zagoat_runner.grading import Kind, Outcome, grade
from zagoat_runner.taskspec import TaskSpec, load_tasks


def run_job(
    executor: Executor, settings: Settings, task: TaskSpec, kind: Kind, files: dict[str, str]
) -> Outcome:
    limit = settings.run_time_limit_seconds if kind == "run" else settings.submit_time_limit_seconds
    job = Job(task=task, kind=kind, files=files, llm_key=f"zagoat-{task.id}-{secrets.token_hex(8)}")
    return grade(
        executor.execute(job, limit),
        kind,
        task.metrics,
        time_limit_seconds=limit,
        memory_limit_mb=settings.memory_limit_mb,
        output_limit_bytes=settings.output_limit_bytes,
    )


def broken_files(task: TaskSpec) -> dict[str, str]:
    """The starter with every module raising on import, to prove errors are reported."""
    return {
        name: ('raise RuntimeError("deliberately broken")\n' if name.endswith(".py") else text)
        for name, text in task.starter_files().items()
    }


def describe(outcome: Outcome) -> str:
    details = [f"{outcome.verdict}: {outcome.message}"]
    details += [
        f"    - {t['name']}: {t['outcome']} {t['message'] or ''}".rstrip()
        for t in outcome.tests
        if t["outcome"] != "passed"
    ]
    details += [
        f"    - metric {m['name']} = {m['value']} (target {m['threshold']})"
        for m in outcome.metrics
    ]
    if outcome.stdout and outcome.verdict != "passed":
        details.append(outcome.stdout[-2000:])
    return "\n".join(details)


def validate_task(executor: Executor, settings: Settings, task: TaskSpec) -> list[str]:
    problems: list[str] = []
    reference = run_job(executor, settings, task, "submit", task.reference_solution())
    if reference.verdict != "passed":
        problems.append(f"reference fails hidden tests: {describe(reference)}")
    sample = run_job(executor, settings, task, "run", task.reference_solution())
    if sample.verdict != "passed":
        problems.append(f"reference fails sample tests: {describe(sample)}")
    starter = run_job(executor, settings, task, "submit", task.starter_files())
    if starter.verdict == "passed":
        problems.append("the untouched starter already passes the hidden tests")
    broken = run_job(executor, settings, task, "submit", broken_files(task))
    if broken.verdict != "error":
        problems.append(f"broken code should be an error, got {describe(broken)}")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    settings = get_settings()
    problems_dir = Path(args[0]) if args else settings.problems_dir
    tasks = load_tasks(problems_dir)
    if not tasks:
        print(f"no tasks found in {problems_dir}", file=sys.stderr)
        return 1
    failures = 0
    with background_mock_llm(problems_dir) as llm_url:
        executor = LocalExecutor(harness_dir=settings.harness_dir, llm_base_url=llm_url)
        for task in tasks.values():
            problems = validate_task(executor, settings, task)
            if problems:
                failures += 1
                print(f"FAIL {task.id}")
                for problem in problems:
                    print(f"  {problem}")
            else:
                print(f"ok   {task.id}")
    print(f"{len(tasks) - failures} of {len(tasks)} task(s) valid")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

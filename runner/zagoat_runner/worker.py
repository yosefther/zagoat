"""The runner worker: pull jobs from Redis, run them in the sandbox, post results to the API.

uv run python -m zagoat_runner.worker
"""

import logging
import threading
import time
from dataclasses import asdict
from typing import Any

import httpx2
from pydantic import ValidationError
from redis import Redis
from redis.exceptions import RedisError

from zagoat_runner.config import Settings, get_settings
from zagoat_runner.executor import Executor, Job
from zagoat_runner.grading import ExecResult, Outcome, grade
from zagoat_runner.jobs import QueuedJob
from zagoat_runner.sandbox import DockerExecutor, check_runtime
from zagoat_runner.taskspec import TaskSpec, load_tasks

log = logging.getLogger("zagoat_runner.worker")

# How long each slot blocks waiting for a job before checking whether to stop.
BLOCK_SECONDS = 5


class ApiClient:
    """Posts job status and results to the API's internal routes."""

    def __init__(self, settings: Settings, http: httpx2.Client | None = None) -> None:
        self.settings = settings
        self.http = http or httpx2.Client(base_url=settings.api_url, timeout=15)

    def _post(self, path: str, body: dict[str, Any]) -> bool:
        delay = 1.0
        for attempt in range(1, self.settings.result_post_attempts + 1):
            try:
                response = self.http.post(
                    path, json=body, headers={"X-Worker-Secret": self.settings.worker_secret}
                )
                if response.status_code < 500:
                    if response.status_code >= 400:
                        log.error(
                            "API refused %s: %s %s", path, response.status_code, response.text
                        )
                    return response.status_code < 400
            except httpx2.HTTPError as exc:
                log.warning("posting %s failed (attempt %d): %s", path, attempt, exc)
            time.sleep(delay)
            delay *= 2
        return False

    def started(self, job_id: str) -> bool:
        return self._post(f"/internal/jobs/{job_id}/started", {})

    def result(self, job_id: str, outcome: Outcome, duration_ms: int) -> bool:
        return self._post(
            f"/internal/jobs/{job_id}/result", {**asdict(outcome), "duration_ms": duration_ms}
        )


def system_error(message: str) -> Outcome:
    return grade(
        ExecResult(exit_code=None, duration_ms=0, system_error=message),
        "submit",
        (),
        time_limit_seconds=0,
        memory_limit_mb=0,
        output_limit_bytes=0,
    )


class Worker:
    def __init__(
        self,
        settings: Settings,
        redis: Redis,
        executor: Executor,
        api: ApiClient,
        tasks: dict[str, TaskSpec],
    ) -> None:
        self.settings = settings
        self.redis = redis
        self.executor = executor
        self.api = api
        self.tasks = tasks
        self.stopping = threading.Event()

    def processing_key(self, slot: int) -> str:
        return f"{self.settings.queue_key}:processing:{slot}"

    def recover(self) -> None:
        """Put jobs a crashed worker left half-done back on the queue (oldest first)."""
        for slot in range(self.settings.concurrency):
            while self.redis.lmove(
                self.processing_key(slot), self.settings.queue_key, "RIGHT", "RIGHT"
            ):
                log.warning("requeued an unfinished job from slot %d", slot)

    def handle(self, raw: bytes | str) -> None:
        try:
            job = QueuedJob.model_validate_json(raw)
        except ValidationError:
            log.error("dropping malformed job: %r", raw[:200])
            return
        age = time.time() - job.enqueued_at
        if age > self.settings.max_queue_age_seconds:
            log.warning("job %s waited %.0fs; reporting system_error", job.job_id, age)
            self.api.result(job.job_id, system_error("waited too long in the queue"), 0)
            return
        task = self.tasks.get(job.problem_id)
        if task is None:
            self.api.result(job.job_id, system_error(f"unknown problem {job.problem_id}"), 0)
            return
        self.api.started(job.job_id)
        limit = (
            self.settings.run_time_limit_seconds
            if job.kind == "run"
            else self.settings.submit_time_limit_seconds
        )
        llm_key = f"zagoat-{job.problem_id}-{job.job_id}"
        try:
            result = self.executor.execute(Job(task, job.kind, job.files, llm_key), limit)
        except Exception as exc:  # A bug here must not kill the worker thread.
            log.exception("executor crashed on job %s", job.job_id)
            result = ExecResult(exit_code=None, duration_ms=0, system_error=repr(exc))
        finally:
            self._clear_llm_log(llm_key)
        outcome = grade(
            result,
            job.kind,
            task.metrics,
            time_limit_seconds=limit,
            memory_limit_mb=self.settings.memory_limit_mb,
            output_limit_bytes=self.settings.output_limit_bytes,
        )
        log.info("job %s %s: %s in %dms", job.job_id, job.kind, outcome.verdict, result.duration_ms)
        self.api.result(job.job_id, outcome, result.duration_ms)

    def _clear_llm_log(self, llm_key: str) -> None:
        try:
            httpx2.delete(
                f"{self.settings.worker_llm_url}/_calls",
                headers={"Authorization": f"Bearer {llm_key}"},
                timeout=5,
            )
        except httpx2.HTTPError:
            log.warning("couldn't clear the mock LLM log for %s", llm_key)

    def run_slot(self, slot: int) -> None:
        processing = self.processing_key(slot)
        while not self.stopping.is_set():
            try:
                raw = self.redis.blmove(
                    self.settings.queue_key, processing, BLOCK_SECONDS, "RIGHT", "LEFT"
                )
            except RedisError as exc:
                log.warning("slot %d: Redis unavailable (%s); retrying", slot, exc)
                self.stopping.wait(2)
                continue
            if raw is None:
                continue
            try:
                self.handle(raw)
            finally:
                self.redis.lrem(processing, 1, raw)  # type: ignore[arg-type]

    def run_forever(self) -> None:
        self.recover()
        threads = [
            threading.Thread(target=self.run_slot, args=(slot,), name=f"slot-{slot}", daemon=True)
            for slot in range(self.settings.concurrency)
        ]
        for thread in threads:
            thread.start()
        log.info("worker started with %d slots", len(threads))
        try:
            while any(thread.is_alive() for thread in threads):
                time.sleep(1)
        except KeyboardInterrupt:
            self.stopping.set()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    if settings.is_production:
        unpinned = [ref for ref in settings.images.values() if "@sha256:" not in ref]
        if unpinned:
            raise SystemExit(f"Production images must be pinned by digest: {unpinned}")
    executor = DockerExecutor(settings, use_gvisor=check_runtime(settings))
    worker = Worker(
        settings,
        # The socket timeout must outlast the blocking wait for a job.
        Redis.from_url(settings.redis_url, socket_timeout=BLOCK_SECONDS + 10),
        executor,
        ApiClient(settings),
        load_tasks(settings.problems_dir),
    )
    worker.run_forever()


if __name__ == "__main__":
    main()

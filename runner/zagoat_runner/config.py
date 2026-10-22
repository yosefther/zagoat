"""Runner configuration. Every sandbox limit and timeout lives here (brief, sections 5 and 9)."""

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
# Production refuses a shorter WORKER_SECRET, or the example value from .env.example.
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    environment: str = "development"

    problems_dir: Path = REPO_ROOT / "problems"
    harness_dir: Path = Path(__file__).resolve().parents[1] / "harness"

    # Sandbox limits.
    run_time_limit_seconds: int = 30
    submit_time_limit_seconds: int = 120
    memory_limit_mb: int = 2048
    cpus: float = 1.0
    pids_limit: int = 64  # proposed
    tmp_size_mb: int = 200  # proposed
    output_limit_bytes: int = 64 * 1024  # proposed

    # Extra time for the container to start before the time limit applies.
    startup_grace_seconds: int = 10
    max_results_bytes: int = 2_000_000

    # Mock LLM: where it serves, and how sandboxes and the worker reach it.
    mock_llm_host: str = "127.0.0.1"
    mock_llm_port: int = 8090
    sandbox_llm_base_url: str = "http://mockllm:8090/v1"
    worker_llm_url: str = "http://127.0.0.1:8090"

    # Docker sandbox (brief, section 5).
    docker_binary: str = "docker"
    sandbox_network: str = "zagoat-sandbox"
    sandbox_user: str = "10001:10001"
    # problem.yaml image name -> image reference. Production must pin by digest.
    images: dict[str, str] = {"zagoat-py312-ml": "zagoat-py312-ml:dev"}
    jobs_dir: Path = Path("/tmp/zagoat-jobs")  # noqa: S108 (per-job folders, removed after)

    # Queue and worker.
    redis_url: str = "redis://localhost:6379/0"
    queue_key: str = "zagoat:jobs"
    max_queue_age_seconds: int = 300
    # Jobs at once. At 2 GB per job an 8 GB server runs about 3 (section 9).
    concurrency: int = 3
    api_url: str = "http://localhost:8000"
    worker_secret: str = "dev-only-worker-secret"  # noqa: S105
    result_post_attempts: int = 4

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _require_a_real_secret_in_production(self) -> Self:
        secret = self.worker_secret
        weak = len(secret) < MIN_SECRET_LENGTH or secret.startswith("dev-only")
        if self.is_production and weak:
            raise ValueError(
                f"Production needs a random WORKER_SECRET of at least {MIN_SECRET_LENGTH} "
                "characters"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

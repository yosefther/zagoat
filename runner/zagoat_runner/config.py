"""Runner configuration. Every sandbox limit and timeout lives here (brief, sections 5 and 9)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


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

    # Mock LLM.
    mock_llm_host: str = "127.0.0.1"
    mock_llm_port: int = 8090


@lru_cache
def get_settings() -> Settings:
    return Settings()

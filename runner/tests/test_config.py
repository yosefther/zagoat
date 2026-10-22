import pytest
from pydantic import ValidationError

from zagoat_runner.config import Settings


def test_development_accepts_the_example_secret() -> None:
    assert Settings(_env_file=None).worker_secret.startswith("dev-only")


@pytest.mark.parametrize("secret", ["dev-only-worker-secret", "short-secret"])
def test_production_refuses_example_or_short_secrets(secret: str) -> None:
    with pytest.raises(ValidationError, match="WORKER_SECRET"):
        Settings(_env_file=None, environment="production", worker_secret=secret)


def test_production_accepts_a_long_random_secret() -> None:
    assert Settings(_env_file=None, environment="production", worker_secret="w" * 40).is_production

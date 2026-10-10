from datetime import UTC, datetime

import pytest
from redis import Redis

from app import ratelimit


def freeze(monkeypatch: pytest.MonkeyPatch, moment: datetime) -> None:
    monkeypatch.setattr(ratelimit, "utcnow", lambda: moment)


def test_counts_within_a_window_then_blocks(redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    freeze(monkeypatch, datetime(2026, 1, 1, 10, 15, tzinfo=UTC))

    results = [ratelimit.hit(redis, "t", "ip", limit=2, window_seconds=3600) for _ in range(3)]

    assert [r.allowed for r in results] == [True, True, False]
    assert results[-1].retry_after_seconds == 45 * 60


def test_new_window_resets_the_count(redis: Redis, monkeypatch: pytest.MonkeyPatch) -> None:
    freeze(monkeypatch, datetime(2026, 1, 1, 10, 59, tzinfo=UTC))
    for _ in range(3):
        ratelimit.hit(redis, "t", "ip", limit=2, window_seconds=3600)

    freeze(monkeypatch, datetime(2026, 1, 1, 11, 0, tzinfo=UTC))

    assert ratelimit.hit(redis, "t", "ip", limit=2, window_seconds=3600).allowed


def test_subjects_are_counted_separately(redis: Redis) -> None:
    ratelimit.hit(redis, "t", "a", limit=1, window_seconds=3600)

    assert ratelimit.hit(redis, "t", "b", limit=1, window_seconds=3600).allowed
    assert ratelimit.peek(redis, "t", "a", window_seconds=3600) == 1

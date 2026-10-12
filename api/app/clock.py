from datetime import UTC, datetime


def utcnow() -> datetime:
    """The single source of "now", so tests can move time."""
    return datetime.now(UTC)

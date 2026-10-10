from alembic import context
from sqlalchemy import Connection

from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import get_settings
from app.db import Base, get_engine

target_metadata = Base.metadata


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests pass their own connection so migrations run against the test database.
    connection = context.config.attributes.get("connection")
    if connection is not None:
        run_migrations(connection)
        return
    with get_engine(get_settings()).connect() as connection:
        run_migrations(connection)


if context.is_offline_mode():
    raise SystemExit("Offline migrations are not supported; run against a live database.")
run_migrations_online()

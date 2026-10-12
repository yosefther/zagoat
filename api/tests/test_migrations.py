from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

from tests.conftest import ALEMBIC_INI


def test_migrations_downgrade_and_upgrade_cleanly(engine: Engine) -> None:
    with engine.begin() as connection:
        config = Config(ALEMBIC_INI)
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        command.upgrade(config, "head")

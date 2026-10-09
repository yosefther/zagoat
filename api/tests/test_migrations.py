from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from app.config import Settings

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def test_migrations_upgrade_and_downgrade_cleanly(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        config = Config(ALEMBIC_INI)
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        command.upgrade(config, "head")
    engine.dispose()

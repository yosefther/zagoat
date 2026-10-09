"""baseline

Revision ID: 327ef8ae883e
Revises:
Create Date: 2026-10-21 20:37:22.309992

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "327ef8ae883e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

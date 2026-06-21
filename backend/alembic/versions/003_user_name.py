"""add user display name

Revision ID: 003
Revises: 002
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("name", sa.String(length=255), nullable=False, server_default=""),
    )
    op.execute(
        "UPDATE users SET name = split_part(email, '@', 1) WHERE name = '' OR name IS NULL"
    )
    op.alter_column("users", "name", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "name")

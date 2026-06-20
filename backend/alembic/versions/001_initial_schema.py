"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('field_worker', 'manager')",
            name="ck_users_role",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("program_area", sa.String(length=255), nullable=False),
        sa.Column("stakeholders", sa.Text(), server_default="", nullable=False),
        sa.Column("raw_notes", sa.Text(), server_default="", nullable=False),
        sa.Column("note_image_path", sa.String(length=512), nullable=True),
        sa.Column("voice_memo_path", sa.String(length=512), nullable=True),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sentiment IN ('positive', 'neutral', 'negative') OR sentiment IS NULL",
            name="ck_visits_sentiment",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_visits_visit_date", "visits", ["visit_date"], unique=False)
    op.create_index("idx_visits_program_area", "visits", ["program_area"], unique=False)
    op.create_index("idx_visits_location", "visits", ["location"], unique=False)
    op.create_index("idx_visits_sentiment", "visits", ["sentiment"], unique=False)

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=50), server_default="text", nullable=False),
        sa.CheckConstraint(
            "type IN ('finding', 'blocker', 'follow_up')",
            name="ck_findings_type",
        ),
        sa.CheckConstraint(
            "source IN ('text', 'photo', 'voice')",
            name="ck_findings_source",
        ),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_findings_type", "findings", ["type"], unique=False)
    op.create_index("idx_findings_category", "findings", ["category"], unique=False)
    op.create_index("idx_findings_visit_id", "findings", ["visit_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_findings_visit_id", table_name="findings")
    op.drop_index("idx_findings_category", table_name="findings")
    op.drop_index("idx_findings_type", table_name="findings")
    op.drop_table("findings")

    op.drop_index("idx_visits_sentiment", table_name="visits")
    op.drop_index("idx_visits_location", table_name="visits")
    op.drop_index("idx_visits_program_area", table_name="visits")
    op.drop_index("idx_visits_visit_date", table_name="visits")
    op.drop_table("visits")

    op.drop_table("users")

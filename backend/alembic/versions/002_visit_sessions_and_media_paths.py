"""visit sessions and multi-path media on visits

Revision ID: 002
Revises: 001
Create Date: 2026-06-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "visit_sessions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("program_area", sa.String(length=255), nullable=False),
        sa.Column("stakeholders", sa.Text(), server_default="", nullable=False),
        sa.Column("raw_notes", sa.Text(), server_default="", nullable=False),
        sa.Column("note_image_paths", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("field_photo_paths", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("voice_memo_paths", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("debrief", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="preprocessed", nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("session_id"),
    )

    op.add_column("visits", sa.Column("note_image_paths", sa.JSON(), nullable=True))
    op.add_column("visits", sa.Column("field_photo_paths", sa.JSON(), nullable=True))
    op.add_column("visits", sa.Column("voice_memo_paths", sa.JSON(), nullable=True))

    op.execute(
        """
        UPDATE visits
        SET note_image_paths = CASE
            WHEN note_image_path IS NOT NULL THEN json_build_array(note_image_path)
            ELSE '[]'::json
        END,
        voice_memo_paths = CASE
            WHEN voice_memo_path IS NOT NULL THEN json_build_array(voice_memo_path)
            ELSE '[]'::json
        END,
        field_photo_paths = '[]'::json
        """
    )

    op.drop_column("visits", "note_image_path")
    op.drop_column("visits", "voice_memo_path")


def downgrade() -> None:
    op.add_column("visits", sa.Column("note_image_path", sa.String(length=512), nullable=True))
    op.add_column("visits", sa.Column("voice_memo_path", sa.String(length=512), nullable=True))

    op.execute(
        """
        UPDATE visits
        SET note_image_path = note_image_paths->>0,
            voice_memo_path = voice_memo_paths->>0
        WHERE note_image_paths IS NOT NULL OR voice_memo_paths IS NOT NULL
        """
    )

    op.drop_column("visits", "note_image_paths")
    op.drop_column("visits", "field_photo_paths")
    op.drop_column("visits", "voice_memo_paths")
    op.drop_table("visit_sessions")

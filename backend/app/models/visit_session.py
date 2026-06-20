from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.database import Base


class VisitSession(Base):
    """In-progress visit workflow state linking preprocess → debrief → save."""

    __tablename__ = "visit_sessions"

    session_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    program_area: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholders: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    note_image_paths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    field_photo_paths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    voice_memo_paths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    debrief: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="preprocessed")
    visit_id: Mapped[int | None] = mapped_column(
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

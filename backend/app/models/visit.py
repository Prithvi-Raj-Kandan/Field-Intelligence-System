from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        CheckConstraint(
            "sentiment IN ('positive', 'neutral', 'negative') OR sentiment IS NULL",
            name="ck_visits_sentiment",
        ),
        Index("idx_visits_visit_date", "visit_date"),
        Index("idx_visits_program_area", "program_area"),
        Index("idx_visits_location", "location"),
        Index("idx_visits_sentiment", "sentiment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    program_area: Mapped[str] = mapped_column(String(255), nullable=False)
    stakeholders: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    note_image_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    field_photo_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    voice_memo_paths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="visits")
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
    )

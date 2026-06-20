from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        CheckConstraint(
            "type IN ('finding', 'blocker', 'follow_up')",
            name="ck_findings_type",
        ),
        CheckConstraint(
            "source IN ('text', 'photo', 'voice')",
            name="ck_findings_source",
        ),
        Index("idx_findings_type", "type"),
        Index("idx_findings_category", "category"),
        Index("idx_findings_visit_id", "visit_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    visit_id: Mapped[int] = mapped_column(
        ForeignKey("visits.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="text")

    visit: Mapped["Visit"] = relationship(back_populates="findings")

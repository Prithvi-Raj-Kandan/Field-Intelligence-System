"""CSV export of visits for manager reporting."""

import csv
import io
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.user import User
from app.models.visit import Visit


def _visit_filters(
    *,
    date_from: date | None,
    date_to: date | None,
    program_area: str | None,
    location: str | None,
    worker_id: int | None = None,
):
    clauses = []
    if date_from is not None:
        clauses.append(Visit.visit_date >= date_from)
    if date_to is not None:
        clauses.append(Visit.visit_date <= date_to)
    if program_area:
        clauses.append(Visit.program_area == program_area.strip())
    if location:
        clauses.append(Visit.location.ilike(f"%{location.strip()}%"))
    if worker_id is not None:
        clauses.append(Visit.user_id == worker_id)
    return clauses


def export_visits_csv(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    worker_id: int | None = None,
) -> str:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
    )

    blocker_count = (
        select(func.count(Finding.id))
        .where(Finding.visit_id == Visit.id, Finding.type == "blocker")
        .correlate(Visit)
        .scalar_subquery()
    )

    stmt = (
        select(Visit, User.name, User.email, blocker_count.label("blocker_count"))
        .join(User, Visit.user_id == User.id)
        .where(*filters)
        .order_by(Visit.visit_date.desc(), Visit.created_at.desc())
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "visit_id",
            "location",
            "visit_date",
            "program_area",
            "sentiment",
            "worker_name",
            "worker_email",
            "blocker_count",
            "stakeholders",
            "raw_notes",
        ]
    )

    for visit, worker_name, worker_email, blockers in db.execute(stmt).all():
        writer.writerow(
            [
                visit.id,
                visit.location,
                visit.visit_date.isoformat(),
                visit.program_area,
                visit.sentiment or "",
                worker_name,
                worker_email,
                int(blockers or 0),
                visit.stakeholders.replace("\n", " ").strip(),
                visit.raw_notes.replace("\n", " ").strip(),
            ]
        )

    return output.getvalue()

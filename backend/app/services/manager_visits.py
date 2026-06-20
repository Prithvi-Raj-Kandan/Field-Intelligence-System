"""Manager-facing visit list and detail queries."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.finding import Finding
from app.models.visit import Visit
from app.schemas.debrief import DebriefItem
from app.schemas.visit import (
    FindingDetail,
    ManagerVisitDetail,
    PaginatedVisitsResponse,
    VisitListItem,
)


def _visit_filters(
    *,
    date_from: date | None,
    date_to: date | None,
    program_area: str | None,
    location: str | None,
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
    return clauses


def _blocker_count_subquery():
    return (
        select(func.count(Finding.id))
        .where(Finding.visit_id == Visit.id, Finding.type == "blocker")
        .correlate(Visit)
        .scalar_subquery()
    )


def list_visits_for_manager(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedVisitsResponse:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
    )

    total = db.scalar(select(func.count()).select_from(Visit).where(*filters)) or 0

    blocker_count = _blocker_count_subquery()
    stmt = (
        select(Visit, blocker_count.label("blocker_count"))
        .where(*filters)
        .order_by(Visit.visit_date.desc(), Visit.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    items: list[VisitListItem] = []
    for visit, count in db.execute(stmt).all():
        items.append(
            VisitListItem(
                id=visit.id,
                location=visit.location,
                visit_date=visit.visit_date,
                program_area=visit.program_area,
                sentiment=visit.sentiment,
                created_at=visit.created_at,
                blocker_count=int(count or 0),
            )
        )

    return PaginatedVisitsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def _media_urls(base_url: str, paths: list[str]) -> list[str]:
    base = base_url.rstrip("/")
    return [f"{base}/media/{path.lstrip('/')}" for path in paths if path]


def get_visit_for_manager(
    db: Session,
    visit_id: int,
    *,
    base_url: str,
) -> ManagerVisitDetail | None:
    visit = db.scalar(
        select(Visit)
        .options(selectinload(Visit.findings))
        .where(Visit.id == visit_id)
    )
    if visit is None:
        return None

    note_paths = visit.note_image_paths or []
    field_paths = visit.field_photo_paths or []
    voice_paths = visit.voice_memo_paths or []

    findings = [
        FindingDetail(
            id=f.id,
            type=f.type,  # type: ignore[arg-type]
            text=f.text,
            source=f.source,  # type: ignore[arg-type]
            category=f.category,
        )
        for f in visit.findings
    ]

    return ManagerVisitDetail(
        id=visit.id,
        location=visit.location,
        visit_date=visit.visit_date,
        program_area=visit.program_area,
        sentiment=visit.sentiment,
        created_at=visit.created_at,
        stakeholders=visit.stakeholders,
        raw_notes=visit.raw_notes,
        note_image_paths=note_paths,
        field_photo_paths=field_paths,
        voice_memo_paths=voice_paths,
        note_image_urls=_media_urls(base_url, note_paths),
        field_photo_urls=_media_urls(base_url, field_paths),
        voice_memo_urls=_media_urls(base_url, voice_paths),
        findings=findings,
    )


def visit_to_worker_detail(visit: Visit) -> dict:
    """Shared field mapping for worker GET /visits/mine/{id}."""
    findings = [
        DebriefItem(type=f.type, text=f.text, source=f.source)  # type: ignore[arg-type]
        for f in visit.findings
    ]
    return {
        "id": visit.id,
        "location": visit.location,
        "visit_date": visit.visit_date,
        "program_area": visit.program_area,
        "sentiment": visit.sentiment,
        "created_at": visit.created_at,
        "stakeholders": visit.stakeholders,
        "raw_notes": visit.raw_notes,
        "note_image_paths": visit.note_image_paths or [],
        "field_photo_paths": visit.field_photo_paths or [],
        "voice_memo_paths": visit.voice_memo_paths or [],
        "findings": findings,
    }

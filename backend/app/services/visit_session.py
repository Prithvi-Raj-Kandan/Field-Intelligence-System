"""Persist and load in-progress visit workflow sessions."""

from datetime import date

from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.visit import Visit
from app.models.visit_session import VisitSession
from app.schemas.debrief import DebriefResult, VisitStructuredInput


class SessionNotFoundError(LookupError):
    pass


class SessionAccessError(PermissionError):
    pass


class SessionStateError(ValueError):
    pass


def get_session_for_user(db: Session, session_id: str, user_id: int) -> VisitSession:
    session = db.get(VisitSession, session_id)
    if session is None:
        raise SessionNotFoundError(f"Visit session not found: {session_id}")
    if session.user_id != user_id:
        raise SessionAccessError("Visit session belongs to another user")
    return session


def create_preprocess_session(
    db: Session,
    *,
    user_id: int,
    location: str,
    visit_date: date,
    program_area: str,
    stakeholders: str,
    raw_notes: str,
    note_image_paths: list[str],
) -> VisitSession:
    row = VisitSession(
        user_id=user_id,
        location=location.strip(),
        visit_date=visit_date,
        program_area=program_area.strip(),
        stakeholders=stakeholders.strip(),
        raw_notes=raw_notes,
        note_image_paths=note_image_paths,
        field_photo_paths=[],
        voice_memo_paths=[],
        debrief=None,
        status="preprocessed",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def structured_from_session(session: VisitSession) -> VisitStructuredInput:
    return VisitStructuredInput(
        location=session.location,
        visit_date=session.visit_date.isoformat(),
        program_area=session.program_area,
        stakeholders=session.stakeholders,
    )


def update_session_for_debrief(
    db: Session,
    session: VisitSession,
    *,
    raw_notes: str | None,
    field_photo_paths: list[str],
    voice_memo_paths: list[str],
    debrief: DebriefResult,
) -> VisitSession:
    if raw_notes is not None:
        session.raw_notes = raw_notes.strip()
    session.field_photo_paths = field_photo_paths
    session.voice_memo_paths = voice_memo_paths
    session.debrief = debrief.model_dump()
    session.status = "debrief_ready"
    db.commit()
    db.refresh(session)
    return session


def save_visit_from_session(
    db: Session,
    session: VisitSession,
    *,
    user_id: int,
    raw_notes: str | None,
    debrief: DebriefResult,
) -> Visit:
    if session.status == "saved":
        raise SessionStateError("Visit session was already saved")
    if session.status != "debrief_ready":
        raise SessionStateError("Complete debrief generation before saving")

    final_notes = raw_notes.strip() if raw_notes is not None else session.raw_notes

    visit = Visit(
        user_id=user_id,
        location=session.location,
        visit_date=session.visit_date,
        program_area=session.program_area,
        stakeholders=session.stakeholders,
        raw_notes=final_notes,
        note_image_paths=session.note_image_paths or [],
        field_photo_paths=session.field_photo_paths or [],
        voice_memo_paths=session.voice_memo_paths or [],
        sentiment=debrief.sentiment,
    )
    db.add(visit)
    db.flush()

    for item in debrief.all_items():
        db.add(
            Finding(
                visit_id=visit.id,
                type=item.type,
                text=item.text,
                source=item.source,
            )
        )

    session.raw_notes = final_notes
    session.debrief = debrief.model_dump()
    session.status = "saved"
    session.visit_id = visit.id
    db.commit()
    db.refresh(visit)
    return visit

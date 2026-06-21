from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.middleware.auth import require_role
from app.models.user import User
from app.models.visit import Visit
from app.models.visit_session import VisitSession
from app.models.finding import Finding
from app.schemas.debrief import VisitStructuredInput
from app.schemas.visit import (
    DebriefResponse,
    GalleryMediaItem,
    ManagerVisitDetail,
    PaginatedVisitsResponse,
    RecordingMediaItem,
    PreprocessVisitResponse,
    SaveVisitRequest,
    SaveVisitResponse,
    VisitDetail,
    VisitSessionStatusResponse,
    VisitSummary,
)
from app.services.manager_visits import (
    get_visit_for_manager,
    list_visits_for_manager,
    visit_to_worker_detail,
)
from app.services.visit_export import export_visits_csv
from app.services.visit_processor import (
    generate_visit_debrief,
    preprocess_freeform_notes,
    save_context_media,
)
from app.services.visit_session import (
    SessionAccessError,
    SessionNotFoundError,
    SessionStateError,
    create_preprocess_session,
    get_session_for_user,
    load_session_debrief,
    save_visit_from_session,
    structured_from_session,
    update_session_for_debrief,
)

router = APIRouter(prefix="/visits", tags=["visits"])

field_worker_required = require_role("field_worker")
manager_required = require_role("manager")


def _structured_from_form(
    location: str,
    visit_date,
    program_area: str,
    stakeholders: str,
) -> VisitStructuredInput:
    return VisitStructuredInput(
        location=location.strip(),
        visit_date=visit_date.isoformat(),
        program_area=program_area.strip(),
        stakeholders=stakeholders.strip(),
    )


def _map_session_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SessionNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SessionAccessError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, SessionStateError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    raise exc


def _merge_note_uploads(
    note_image: UploadFile | None,
    note_images: list[UploadFile],
) -> list[UploadFile]:
    merged = list(note_images)
    if note_image and note_image.filename:
        merged.insert(0, note_image)
    return merged


@router.get("/mine", response_model=list[VisitSummary])
def list_my_visits(
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> list[VisitSummary]:
    visits = db.scalars(
        select(Visit)
        .where(Visit.user_id == current_user.id)
        .order_by(Visit.visit_date.desc(), Visit.created_at.desc())
    ).all()
    return list(visits)


@router.get("/mine/gallery", response_model=list[GalleryMediaItem])
def list_my_gallery(
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> list[GalleryMediaItem]:
    visits = db.scalars(
        select(Visit).where(Visit.user_id == current_user.id).order_by(Visit.created_at.desc())
    ).all()
    items: list[GalleryMediaItem] = []
    for visit in visits:
        for path in visit.field_photo_paths or []:
            items.append(
                GalleryMediaItem(
                    visit_id=visit.id,
                    path=path,
                    media_type="field",
                    location=visit.location,
                    visit_date=visit.visit_date,
                )
            )
    return items


@router.get("/mine/recordings", response_model=list[RecordingMediaItem])
def list_my_recordings(
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RecordingMediaItem]:
    """Voice memos from saved field visits."""
    visits = db.scalars(
        select(Visit).where(Visit.user_id == current_user.id).order_by(Visit.created_at.desc())
    ).all()
    items: list[RecordingMediaItem] = []
    for visit in visits:
        for path in visit.voice_memo_paths or []:
            items.append(
                RecordingMediaItem(
                    visit_id=visit.id,
                    path=path,
                    location=visit.location,
                    visit_date=visit.visit_date,
                )
            )
    return items


@router.get("/mine/{visit_id}", response_model=VisitDetail)
def get_my_visit(
    visit_id: int,
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> VisitDetail:
    visit = db.scalar(
        select(Visit)
        .options(selectinload(Visit.findings))
        .where(Visit.id == visit_id, Visit.user_id == current_user.id)
    )
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    return VisitDetail(**visit_to_worker_detail(visit))


@router.get("", response_model=PaginatedVisitsResponse)
def list_visits(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    program_area: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    worker_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedVisitsResponse:
    """Paginated visit list for managers (all workers)."""
    _ = current_user
    return list_visits_for_manager(
        db,
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
        page=page,
        page_size=page_size,
    )


@router.get("/export.csv")
def export_visits(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    program_area: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    worker_id: Annotated[int | None, Query()] = None,
) -> Response:
    """Download filtered visits as CSV."""
    _ = current_user
    csv_body = export_visits_csv(
        db,
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
    )
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="visits-export.csv"'},
    )


@router.get("/{visit_id}", response_model=ManagerVisitDetail)
def get_visit(
    visit_id: int,
    request: Request,
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
) -> ManagerVisitDetail:
    """Full visit detail for manager drill-down."""
    _ = current_user
    detail = get_visit_for_manager(db, visit_id, base_url=str(request.base_url))
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return detail


@router.get("/sessions/{session_id}", response_model=VisitSessionStatusResponse)
def get_visit_session(
    session_id: str,
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> VisitSessionStatusResponse:
    """Return workflow session state — recover debrief if generation succeeded but the client errored."""
    try:
        session = get_session_for_user(db, session_id, current_user.id)
    except (SessionNotFoundError, SessionAccessError) as exc:
        raise _map_session_error(exc) from exc

    return VisitSessionStatusResponse(
        session_id=session.session_id,
        status=session.status,
        raw_notes=session.raw_notes,
        debrief=load_session_debrief(session),
    )


@router.post(
    "/preprocess",
    response_model=PreprocessVisitResponse,
    summary="Step 1 — structured fields + free-form notes (text or images)",
)
async def preprocess_visit(
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
    location: Annotated[str, Form()],
    visit_date: Annotated[date, Form(description="Visit date (YYYY-MM-DD)")],
    program_area: Annotated[str, Form()],
    stakeholders: Annotated[str, Form()],
    raw_notes: Annotated[
        str | None,
        Form(description="Typed free-form notes"),
    ] = None,
    note_image: Annotated[
        UploadFile | None,
        File(description="Single note photo (Swagger-friendly)"),
    ] = None,
    note_images: Annotated[
        list[UploadFile],
        File(description="Photos of handwritten/printed notes — transcribed only"),
    ] = [],
) -> PreprocessVisitResponse:
    """
    Upload structured visit data and free-form notes (typed text and/or note photos).

    Note photos are transcribed to `raw_notes`. Field context photos and voice memos are
    **not** accepted here — they are uploaded at `/visits/debrief` and sent directly to the AI.

    Returns `session_id` for subsequent steps (frontend passes this on each Next click).
    `needs_review` is true when note images were transcribed; skip the edit screen when false.
    """
    structured = _structured_from_form(location, visit_date, program_area, stakeholders)

    try:
        result = await preprocess_freeform_notes(
            structured=structured,
            typed_notes=(raw_notes or "").strip(),
            note_images=_merge_note_uploads(note_image, note_images),
        )
        session = create_preprocess_session(
            db,
            user_id=current_user.id,
            location=location,
            visit_date=visit_date,
            program_area=program_area,
            stakeholders=stakeholders,
            raw_notes=result.raw_notes,
            note_image_paths=result.note_image_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Preprocessing failed: {exc}",
        ) from exc

    return PreprocessVisitResponse(
        session_id=session.session_id,
        raw_notes=result.raw_notes,
        needs_review=result.needs_review,
    )


@router.post(
    "/debrief",
    response_model=DebriefResponse,
    summary="Step 2 — debrief from notes + context photos/voice (direct AI interpretation)",
)
async def create_visit_debrief(
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
    session_id: Annotated[str, Form(description="Session from /visits/preprocess")],
    raw_notes: Annotated[
        str | None,
        Form(description="Edited notes — omit to use session value"),
    ] = None,
    field_photo: Annotated[
        UploadFile | None,
        File(description="Single field photo (Swagger-friendly)"),
    ] = None,
    field_photos: Annotated[
        list[UploadFile],
        File(description="Field context photos — interpreted directly, not transcribed"),
    ] = [],
    voice_memo: Annotated[
        UploadFile | None,
        File(description="Single voice memo (Swagger-friendly)"),
    ] = None,
    voice_memos: Annotated[
        list[UploadFile],
        File(description="Voice memos — interpreted directly, not transcribed"),
    ] = [],
) -> DebriefResponse:
    """
    Generate the debrief using session text plus field photos and voice memos.

    Pass `session_id` from preprocess. Optionally pass edited `raw_notes`. Upload context
    media here — they are not converted to text. Returns debrief linked to the same session.
    """
    try:
        session = get_session_for_user(db, session_id, current_user.id)
        if session.status == "saved":
            raise SessionStateError("Visit session was already saved")

        # Idempotent: a duplicate or retried request returns the stored debrief.
        existing = load_session_debrief(session)
        if session.status == "debrief_ready" and existing is not None:
            if raw_notes is not None:
                session.raw_notes = raw_notes.strip()
                db.commit()
            return DebriefResponse(session_id=session.session_id, debrief=existing)

        field_paths, voice_paths = await save_context_media(
            field_photos=_merge_note_uploads(field_photo, field_photos),
            voice_memos=_merge_note_uploads(voice_memo, voice_memos),
        )

        notes = raw_notes.strip() if raw_notes is not None else session.raw_notes
        result = generate_visit_debrief(
            structured=structured_from_session(session),
            raw_notes=notes,
            note_image_paths=session.note_image_paths or [],
            field_photo_paths=field_paths,
            voice_memo_paths=voice_paths,
        )

        update_session_for_debrief(
            db,
            session,
            raw_notes=result.raw_notes,
            field_photo_paths=field_paths,
            voice_memo_paths=voice_paths,
            debrief=result.debrief,
        )
    except (SessionNotFoundError, SessionAccessError, SessionStateError, ValueError) as exc:
        raise _map_session_error(exc) from exc
    except RuntimeError as exc:
        # If Gemini failed after a concurrent request succeeded, return cached debrief.
        session = db.get(VisitSession, session_id)
        if session and session.user_id == current_user.id:
            cached = load_session_debrief(session)
            if session.status == "debrief_ready" and cached is not None:
                return DebriefResponse(session_id=session.session_id, debrief=cached)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Debrief generation failed: {exc}",
        ) from exc

    return DebriefResponse(session_id=session.session_id, debrief=result.debrief)


@router.post(
    "/save",
    response_model=SaveVisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Step 3 — persist confirmed visit and debrief",
)
def save_visit(
    body: SaveVisitRequest,
    current_user: Annotated[User, Depends(field_worker_required)],
    db: Annotated[Session, Depends(get_db)],
) -> SaveVisitResponse:
    """
    Save the visit after debrief review. Pass `session_id` from the workflow; optional
    final `raw_notes` and edited `debrief` from the UI.
    """
    try:
        session = get_session_for_user(db, body.session_id, current_user.id)
        visit = save_visit_from_session(
            db,
            session,
            user_id=current_user.id,
            raw_notes=body.raw_notes,
            debrief=body.debrief,
        )
    except (SessionNotFoundError, SessionAccessError, SessionStateError, ValueError) as exc:
        raise _map_session_error(exc) from exc

    return SaveVisitResponse(visit_id=visit.id)

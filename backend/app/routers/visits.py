from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.config import settings
from app.middleware.auth import require_role
from app.models.user import User
from app.schemas.debrief import VisitStructuredInput
from app.schemas.visit import DraftResponse
from app.services.ai import transcribe_image
from app.storage import get_storage_backend
from app.storage.local import StorageError

router = APIRouter(prefix="/visits", tags=["visits"])

field_worker_required = require_role("field_worker")


@router.post("/draft", response_model=DraftResponse)
async def create_visit_draft(
    current_user: Annotated[User, Depends(field_worker_required)],
    location: Annotated[str, Form()],
    visit_date: Annotated[date, Form()],
    program_area: Annotated[str, Form()],
    stakeholders: Annotated[str, Form()],
    raw_notes: Annotated[str | None, Form()] = None,
    note_image: UploadFile | None = File(None),
) -> DraftResponse:
    _ = current_user

    notes = (raw_notes or "").strip()
    has_image = note_image is not None and note_image.filename

    if not notes and not has_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide typed notes, a photo of notes, or both",
        )

    structured = VisitStructuredInput(
        location=location.strip(),
        visit_date=visit_date.isoformat(),
        program_area=program_area.strip(),
        stakeholders=stakeholders.strip(),
    )

    note_image_path: str | None = None
    transcription = notes

    if has_image:
        storage = get_storage_backend()
        try:
            saved = await storage.save_upload(note_image, folder="images")
            note_image_path = saved.path
            resolved_mime = saved.mime_type
        except StorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        image_file = settings.upload_path / note_image_path
        try:
            image_transcription = transcribe_image(
                image_file.read_bytes(),
                mime_type=resolved_mime,
                context=structured,
                filename=note_image.filename,
            )
        except (RuntimeError, ValueError) as exc:
            if note_image_path:
                await storage.delete(note_image_path)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Transcription failed: {exc}",
            ) from exc

        if notes:
            transcription = f"{image_transcription.strip()}\n\n--- Typed notes ---\n{notes}"
        else:
            transcription = image_transcription.strip()

    return DraftResponse(
        transcription=transcription,
        note_image_path=note_image_path,
    )

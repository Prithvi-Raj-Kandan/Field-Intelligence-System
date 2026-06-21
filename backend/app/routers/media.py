from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.media_access import user_can_access_media
from app.storage.local import StorageError
from app.utils.image_mime import GEMINI_IMAGE_MIMES, resolve_audio_mime, resolve_image_mime

router = APIRouter(tags=["media"])


@router.get("/media/{file_path:path}")
async def serve_media(
    file_path: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    if settings.storage_backend.lower() != "local":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not available",
        )

    normalized = file_path.replace("\\", "/")
    if ".." in normalized.split("/") or normalized.startswith("/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not user_can_access_media(db, current_user, normalized):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    full_path = (settings.upload_path / normalized).resolve()
    try:
        if not str(full_path).startswith(str(settings.upload_path.resolve())):
            raise StorageError("Invalid file path")
    except StorageError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from None

    if not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    media_type = _resolve_media_type(full_path)
    return FileResponse(full_path, media_type=media_type)


def _resolve_media_type(full_path: Path) -> str:
    data = full_path.read_bytes()
    name = full_path.name
    rel = str(full_path).replace("\\", "/")
    if "/audio/" in rel or rel.endswith((".mp3", ".wav", ".webm", ".m4a", ".ogg")):
        try:
            return resolve_audio_mime(data, filename=name)
        except ValueError:
            return "application/octet-stream"
    try:
        mime = resolve_image_mime(data, filename=name)
        if mime in GEMINI_IMAGE_MIMES:
            return mime
    except ValueError:
        pass
    return "application/octet-stream"

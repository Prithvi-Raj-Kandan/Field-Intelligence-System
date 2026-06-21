from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.media_access import user_can_access_media
from app.storage import get_storage_backend
from app.storage.local import StorageError
from app.utils.image_mime import GEMINI_IMAGE_MIMES, resolve_audio_mime, resolve_image_mime

router = APIRouter(tags=["media"])


@router.get("/media/{file_path:path}")
async def serve_media(
    file_path: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    normalized = file_path.replace("\\", "/")
    if ".." in normalized.split("/") or normalized.startswith("/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    if not user_can_access_media(db, current_user, normalized):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    storage = get_storage_backend()
    try:
        if not storage.exists(normalized):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        data = storage.read_bytes(normalized)
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from exc

    media_type = _resolve_media_type(data, normalized)
    return Response(content=data, media_type=media_type)


def _resolve_media_type(data: bytes, relative_path: str) -> str:
    name = relative_path.rsplit("/", 1)[-1]
    rel = relative_path.replace("\\", "/")
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

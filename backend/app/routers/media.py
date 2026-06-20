from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.config import settings
from app.storage.local import StorageError
from app.utils.image_mime import GEMINI_IMAGE_MIMES, resolve_image_mime

router = APIRouter(tags=["media"])


@router.get("/media/{file_path:path}")
async def serve_media(file_path: str) -> FileResponse:
    if settings.storage_backend.lower() != "local":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not available",
        )

    normalized = file_path.replace("\\", "/")
    if ".." in normalized.split("/") or normalized.startswith("/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    full_path = (settings.upload_path / normalized).resolve()
    try:
        if not str(full_path).startswith(str(settings.upload_path.resolve())):
            raise StorageError("Invalid file path")
    except StorageError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found") from None

    if not full_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    media_type = resolve_image_mime(
        full_path.read_bytes(),
        filename=full_path.name,
    )
    if media_type not in GEMINI_IMAGE_MIMES:
        media_type = "application/octet-stream"

    return FileResponse(full_path, media_type=media_type)

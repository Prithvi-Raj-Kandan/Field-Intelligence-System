from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.config import settings
from app.storage.local import StorageError

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

    return FileResponse(full_path)

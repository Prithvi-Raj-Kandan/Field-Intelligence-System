import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.storage.base import SavedUpload, StorageBackend
from app.utils.image_mime import (
    GEMINI_IMAGE_MIMES,
    extension_for_mime,
    resolve_image_mime,
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class StorageError(ValueError):
    pass


class LocalStorageBackend(StorageBackend):
    def __init__(self, upload_root: Path | None = None) -> None:
        self.upload_root = upload_root or settings.upload_path

    def _resolve_path(self, relative_path: str) -> Path:
        if ".." in relative_path.replace("\\", "/").split("/"):
            raise StorageError("Invalid file path")
        full_path = (self.upload_root / relative_path).resolve()
        if not str(full_path).startswith(str(self.upload_root.resolve())):
            raise StorageError("Invalid file path")
        return full_path

    async def save_upload(self, file: UploadFile, folder: str) -> SavedUpload:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise StorageError("File exceeds maximum size of 10 MB")

        try:
            mime_type = resolve_image_mime(
                content,
                filename=file.filename,
                declared=file.content_type,
            )
        except ValueError as exc:
            raise StorageError(str(exc)) from exc

        if mime_type not in GEMINI_IMAGE_MIMES:
            raise StorageError(f"Unsupported file type: {mime_type}")

        extension = extension_for_mime(mime_type)
        folder = folder.strip("/\\")
        target_dir = self.upload_root / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}{extension}"
        relative_path = f"{folder}/{filename}"
        full_path = self._resolve_path(relative_path)
        full_path.write_bytes(content)
        await file.close()
        return SavedUpload(path=relative_path, mime_type=mime_type)

    async def get_url(self, path: str) -> str:
        return f"/media/{path}"

    async def delete(self, path: str) -> None:
        full_path = self._resolve_path(path)
        if full_path.exists():
            full_path.unlink()

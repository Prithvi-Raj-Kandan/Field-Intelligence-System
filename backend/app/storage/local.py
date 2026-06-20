import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.storage.base import StorageBackend

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


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

    async def save(self, file: UploadFile, folder: str) -> str:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise StorageError(f"Unsupported file type: {content_type or 'unknown'}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise StorageError("File exceeds maximum size of 10 MB")
        if len(content) == 0:
            raise StorageError("Empty file")

        extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
        if extension is None:
            suffix = Path(file.filename or "").suffix.lower()
            extension = suffix if suffix in {".jpg", ".jpeg", ".png"} else ".jpg"

        folder = folder.strip("/\\")
        target_dir = self.upload_root / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}{extension}"
        relative_path = f"{folder}/{filename}"
        full_path = self._resolve_path(relative_path)
        full_path.write_bytes(content)
        await file.close()
        return relative_path

    async def get_url(self, path: str) -> str:
        return f"/media/{path}"

    async def delete(self, path: str) -> None:
        full_path = self._resolve_path(path)
        if full_path.exists():
            full_path.unlink()

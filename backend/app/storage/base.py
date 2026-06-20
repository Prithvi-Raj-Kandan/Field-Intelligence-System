from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import UploadFile


@dataclass
class SavedUpload:
    path: str
    mime_type: str


class StorageBackend(ABC):
    @abstractmethod
    async def save_upload(self, file: UploadFile, folder: str) -> SavedUpload:
        """Persist file; return path and resolved MIME type for Gemini."""

    async def save(self, file: UploadFile, folder: str) -> str:
        saved = await self.save_upload(file, folder)
        return saved.path

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Return a URL or path clients can use to fetch the file."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove a stored file."""

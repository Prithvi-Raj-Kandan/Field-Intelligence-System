from abc import ABC, abstractmethod

from fastapi import UploadFile


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, folder: str) -> str:
        """Persist file and return a relative path (e.g. images/uuid.jpg)."""

    @abstractmethod
    async def get_url(self, path: str) -> str:
        """Return a URL or path clients can use to fetch the file."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove a stored file."""

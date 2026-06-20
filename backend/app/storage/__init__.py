from functools import lru_cache

from app.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


@lru_cache
def get_storage_backend() -> StorageBackend:
    backend = settings.storage_backend.lower()
    if backend == "local":
        return LocalStorageBackend()
    raise NotImplementedError(f"Storage backend '{backend}' is not implemented yet")

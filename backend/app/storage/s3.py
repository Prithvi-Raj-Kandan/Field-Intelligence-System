import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import settings
from app.storage.base import SavedUpload, StorageBackend
from app.storage.local import MAX_FILE_SIZE_BYTES, StorageError
from app.utils.image_mime import (
    GEMINI_IMAGE_MIMES,
    extension_for_audio_mime,
    extension_for_mime,
    resolve_audio_mime,
    resolve_image_mime,
)


def _normalize_key(path: str) -> str:
    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise StorageError("Invalid file path")
    return normalized


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        if not settings.s3_bucket:
            raise StorageError("S3_BUCKET is required when STORAGE_BACKEND=s3")

        session_kwargs: dict = {"region_name": settings.aws_region}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

        self._bucket = settings.s3_bucket
        self._client = boto3.client("s3", **session_kwargs)

    def _head_or_none(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise StorageError(f"S3 head_object failed: {code}") from exc

    async def save_upload(self, file: UploadFile, folder: str) -> SavedUpload:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise StorageError("File exceeds maximum size of 10 MB")

        folder = folder.strip("/\\")
        is_audio = folder.startswith("audio")

        try:
            if is_audio:
                mime_type = resolve_audio_mime(
                    content,
                    filename=file.filename,
                    declared=file.content_type,
                )
                extension = extension_for_audio_mime(mime_type)
            else:
                mime_type = resolve_image_mime(
                    content,
                    filename=file.filename,
                    declared=file.content_type,
                )
                if mime_type not in GEMINI_IMAGE_MIMES:
                    raise ValueError(f"Unsupported file type: {mime_type}")
                extension = extension_for_mime(mime_type)
        except ValueError as exc:
            raise StorageError(str(exc)) from exc

        relative_path = f"{folder}/{uuid.uuid4()}{extension}"
        key = _normalize_key(relative_path)

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=mime_type,
            )
        except ClientError as exc:
            raise StorageError(f"S3 upload failed: {exc}") from exc

        await file.close()
        return SavedUpload(path=relative_path, mime_type=mime_type)

    async def get_url(self, path: str) -> str:
        return f"/media/{_normalize_key(path)}"

    def read_bytes(self, path: str) -> bytes:
        key = _normalize_key(path)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                raise StorageError(f"File not found: {path}") from exc
            raise StorageError(f"S3 get_object failed: {code}") from exc

    def exists(self, path: str) -> bool:
        return self._head_or_none(_normalize_key(path))

    async def delete(self, path: str) -> None:
        key = _normalize_key(path)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            raise StorageError(f"S3 delete failed: {exc}") from exc

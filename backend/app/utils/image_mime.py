"""Detect and normalize image MIME types for storage and Gemini vision."""

import mimetypes
from pathlib import Path

# MIME types supported by Gemini multimodal + local upload
GEMINI_IMAGE_MIMES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }
)

MIME_ALIASES = {
    "image/jpg": "image/jpeg",
    "image/pjpeg": "image/jpeg",
    "image/x-png": "image/png",
    "image/x-citrix-png": "image/png",
}

EXTENSION_FOR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}

GEMINI_AUDIO_MIMES = frozenset(
    {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
        "audio/mp4",
        "audio/x-m4a",
        "audio/aac",
    }
)

AUDIO_EXTENSION_FOR_MIME = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
}


def _normalize_declared_mime(declared: str | None) -> str | None:
    if not declared:
        return None
    base = declared.split(";")[0].strip().lower()
    return MIME_ALIASES.get(base, base)


def sniff_image_mime(data: bytes) -> str | None:
    """Detect image type from magic bytes (preferred over Content-Type header)."""
    if len(data) >= 3 and data[0:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if len(data) >= 8 and data[0:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12].lower()
        if brand in {b"heic", b"heif", b"mif1", b"msf1"}:
            return "image/heic" if brand != b"heif" else "image/heif"
    return None


def resolve_image_mime(
    data: bytes,
    *,
    filename: str | None = None,
    declared: str | None = None,
) -> str:
    """
    Resolve the MIME type to send to Gemini.
    Priority: magic-byte sniff > normalized Content-Type > filename extension.
    """
    if not data:
        raise ValueError("Empty file")

    sniffed = sniff_image_mime(data)
    if sniffed:
        return sniffed

    declared_norm = _normalize_declared_mime(declared)
    if declared_norm in GEMINI_IMAGE_MIMES:
        return declared_norm

    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        guessed_norm = _normalize_declared_mime(guessed)
        if guessed_norm in GEMINI_IMAGE_MIMES:
            return guessed_norm

        suffix = Path(filename).suffix.lower()
        suffix_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".heic": "image/heic",
            ".heif": "image/heif",
        }
        if suffix_map.get(suffix):
            return suffix_map[suffix]

    raise ValueError(
        f"Unsupported image type (declared={declared!r}, filename={filename!r}). "
        "Use JPEG, PNG, or WebP."
    )


def extension_for_mime(mime_type: str) -> str:
    return EXTENSION_FOR_MIME.get(mime_type, ".jpg")


def resolve_audio_mime(
    data: bytes,
    *,
    filename: str | None = None,
    declared: str | None = None,
) -> str:
    if not data:
        raise ValueError("Empty file")

    declared_norm = _normalize_declared_mime(declared)
    if declared_norm in GEMINI_AUDIO_MIMES:
        return "audio/mpeg" if declared_norm == "audio/mp3" else declared_norm

    if filename:
        guessed, _ = mimetypes.guess_type(filename)
        guessed_norm = _normalize_declared_mime(guessed)
        if guessed_norm in GEMINI_AUDIO_MIMES:
            return "audio/mpeg" if guessed_norm == "audio/mp3" else guessed_norm

        suffix = Path(filename).suffix.lower()
        suffix_map = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".webm": "audio/webm",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac",
        }
        if suffix_map.get(suffix):
            return suffix_map[suffix]

    raise ValueError(
        f"Unsupported audio type (declared={declared!r}, filename={filename!r}). "
        "Use MP3, WAV, WebM, OGG, or M4A."
    )


def extension_for_audio_mime(mime_type: str) -> str:
    return AUDIO_EXTENSION_FOR_MIME.get(mime_type, ".mp3")

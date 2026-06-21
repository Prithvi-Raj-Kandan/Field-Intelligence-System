"""Orchestrate visit preprocessing and debrief generation."""

from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.schemas.debrief import DebriefResult, VisitStructuredInput
from app.services.ai import generate_debrief, transcribe_audio, transcribe_image
from app.storage import get_storage_backend
from app.storage.base import SavedUpload
from app.storage.local import StorageError
from app.utils.image_mime import resolve_audio_mime, resolve_image_mime


@dataclass
class NotePreprocessResult:
    raw_notes: str
    note_image_paths: list[str]
    needs_review: bool


async def _save_files(files: list[UploadFile], folder: str) -> list[SavedUpload]:
    storage = get_storage_backend()
    saved: list[SavedUpload] = []
    for upload in files:
        if upload.filename:
            saved.append(await storage.save_upload(upload, folder=folder))
    return saved


def _filter_uploads(files: list[UploadFile] | None) -> list[UploadFile]:
    if not files:
        return []
    return [f for f in files if f.filename]


def _resolve_upload_path(relative_path: str) -> Path:
    if ".." in relative_path.replace("\\", "/").split("/"):
        raise ValueError(f"Invalid media path: {relative_path}")
    full_path = (settings.upload_path / relative_path).resolve()
    upload_root = settings.upload_path.resolve()
    if not str(full_path).startswith(str(upload_root)):
        raise ValueError(f"Invalid media path: {relative_path}")
    return full_path


def _validate_media_paths(paths: list[str]) -> None:
    for path in paths:
        full_path = _resolve_upload_path(path)
        if not full_path.exists():
            raise ValueError(f"Media file not found: {path}")


def _load_image_media(paths: list[str]) -> list[tuple[bytes, str]]:
    payload: list[tuple[bytes, str]] = []
    for path in paths:
        full_path = _resolve_upload_path(path)
        data = full_path.read_bytes()
        mime = resolve_image_mime(data, filename=path)
        payload.append((data, mime))
    return payload


def _load_audio_media(paths: list[str]) -> list[tuple[bytes, str]]:
    payload: list[tuple[bytes, str]] = []
    for path in paths:
        full_path = _resolve_upload_path(path)
        data = full_path.read_bytes()
        mime = resolve_audio_mime(data, filename=path)
        payload.append((data, mime))
    return payload


def _combine_note_text(typed_notes: str, note_transcriptions: list[str]) -> str:
    if note_transcriptions:
        if len(note_transcriptions) == 1 and not typed_notes.strip():
            return note_transcriptions[0].strip()
        if len(note_transcriptions) == 1:
            return f"{note_transcriptions[0].strip()}\n\n--- Typed notes ---\n{typed_notes.strip()}"
        joined = "\n\n---\n\n".join(t.strip() for t in note_transcriptions if t.strip())
        header = f"[Handwritten notes — {len(note_transcriptions)} images]\n{joined}"
        if typed_notes.strip():
            return f"{header}\n\n--- Typed notes ---\n{typed_notes.strip()}"
        return header
    return typed_notes.strip()


def _append_voice_transcriptions(notes: str, voice_transcriptions: list[str]) -> str:
    if not voice_transcriptions:
        return notes.strip()
    if len(voice_transcriptions) == 1:
        block = f"[Voice memo transcription]\n{voice_transcriptions[0].strip()}"
    else:
        parts = [
            f"Recording {index + 1}:\n{text.strip()}"
            for index, text in enumerate(voice_transcriptions)
            if text.strip()
        ]
        block = f"[Voice memos — {len(parts)} recordings]\n" + "\n\n".join(parts)
    if notes.strip():
        return f"{notes.strip()}\n\n---\n\n{block}"
    return block


def _transcribe_voice_paths(
    paths: list[str],
    structured: VisitStructuredInput,
) -> list[str]:
    transcriptions: list[str] = []
    for path in paths:
        full_path = _resolve_upload_path(path)
        data = full_path.read_bytes()
        mime = resolve_audio_mime(data, filename=path)
        text = transcribe_audio(
            data,
            mime_type=mime,
            context=structured,
            filename=path,
        )
        transcriptions.append(text)
    return transcriptions


async def preprocess_freeform_notes(
    *,
    structured: VisitStructuredInput,
    typed_notes: str = "",
    note_images: list[UploadFile] | None = None,
) -> NotePreprocessResult:
    """
    Step 1: save note images, transcribe handwriting, merge with typed notes.
    Field context photos and voice memos are not handled here.
    """
    note_images = _filter_uploads(note_images)
    typed_notes = typed_notes.strip()

    if not typed_notes and not note_images:
        raise ValueError("Provide typed free-form notes or a photo of notes")

    try:
        saved_notes = await _save_files(note_images, "images/notes")
    except StorageError as exc:
        raise ValueError(str(exc)) from exc

    note_transcriptions: list[str] = []
    for saved, upload in zip(saved_notes, note_images, strict=True):
        image_bytes = (settings.upload_path / saved.path).read_bytes()
        text = transcribe_image(
            image_bytes,
            mime_type=saved.mime_type,
            context=structured,
            filename=upload.filename,
        )
        note_transcriptions.append(text)

    combined_notes = _combine_note_text(typed_notes, note_transcriptions)
    if not combined_notes:
        raise ValueError("No usable note content after processing uploads")

    return NotePreprocessResult(
        raw_notes=combined_notes,
        note_image_paths=[s.path for s in saved_notes],
        needs_review=bool(note_images),
    )


async def save_context_media(
    *,
    field_photos: list[UploadFile] | None = None,
    voice_memos: list[UploadFile] | None = None,
) -> tuple[list[str], list[str]]:
    """Save field context photos and voice memos for direct AI interpretation."""
    field_photos = _filter_uploads(field_photos)
    voice_memos = _filter_uploads(voice_memos)

    try:
        saved_field = await _save_files(field_photos, "images/field")
        saved_voice = await _save_files(voice_memos, "audio")
    except StorageError as exc:
        raise ValueError(str(exc)) from exc

    return (
        [s.path for s in saved_field],
        [s.path for s in saved_voice],
    )


@dataclass
class DebriefGenerationResult:
    debrief: DebriefResult
    raw_notes: str


def generate_visit_debrief(
    *,
    structured: VisitStructuredInput,
    raw_notes: str,
    note_image_paths: list[str] | None = None,
    field_photo_paths: list[str] | None = None,
    voice_memo_paths: list[str] | None = None,
) -> DebriefGenerationResult:
    """
    Step 2: transcribe voice memos into notes, then debrief from text + field photos.
    """
    note_image_paths = note_image_paths or []
    field_photo_paths = field_photo_paths or []
    voice_memo_paths = voice_memo_paths or []

    _validate_media_paths(note_image_paths + field_photo_paths + voice_memo_paths)

    notes = raw_notes.strip()
    if voice_memo_paths:
        voice_texts = _transcribe_voice_paths(voice_memo_paths, structured)
        notes = _append_voice_transcriptions(notes, voice_texts)

    if not notes and not field_photo_paths:
        raise ValueError("Provide notes or at least one context photo/voice memo")

    if not notes:
        notes = (
            "[No written notes provided. Debrief based on structured visit data "
            "and attached context media only.]"
        )

    return DebriefGenerationResult(
        debrief=generate_debrief(
            notes,
            structured=structured,
            has_photo_notes=bool(note_image_paths),
            field_photos=_load_image_media(field_photo_paths),
            voice_memos=[],
        ),
        raw_notes=notes,
    )

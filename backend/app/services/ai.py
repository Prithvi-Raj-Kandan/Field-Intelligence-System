import json
import logging
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings
from app.schemas.debrief import DebriefResult, VisitStructuredInput
from app.utils.image_mime import MIME_ALIASES, resolve_audio_mime, resolve_image_mime

logger = logging.getLogger(__name__)

TRANSCRIPTION_PROMPT = """You are transcribing handwritten field notes from an NGO worker's site visit.
Transcribe all legible text exactly. Preserve bullet points and structure.
If text is illegible, mark as [illegible]. Do not invent content.
Return only the transcribed text, no preamble."""

VOICE_TRANSCRIPTION_PROMPT = """You are transcribing a voice memo from an NGO field worker's site visit.
Transcribe all spoken content exactly. Preserve bullet points and structure when implied.
If speech is unclear, mark as [unclear]. Do not invent content.
Return only the transcribed text, no preamble."""

DEBRIEF_SYSTEM_PROMPT = """You are an NGO field intelligence assistant. Produce a structured debrief summary
from structured visit metadata, unstructured text notes (typed and/or transcribed handwriting),
field visit photos, and voice memos when provided.

Field visit photos show location, people, proof of work, and on-site conditions — interpret them
directly as visual evidence. Voice memos are field recordings — interpret them directly; do not
assume they were transcribed to text.

Your output has exactly four sections (these drive the manager analytics dashboard):
1. Key findings — important observations, community feedback, program outcomes
2. Blockers observed — obstacles preventing progress (infrastructure, bureaucracy, funding, access)
3. Community sentiment — overall community mood: positive, neutral, or negative
4. Suggested follow-ups — concrete next actions; include reasonable follow-ups implied by
   blockers when the notes do not spell them out (mark as suggested action, not invented facts)

Rules:
- Use structured metadata (location, date, program area, stakeholders) to contextualize items
- Combine text notes with direct interpretation of attached photos and voice memos
- Do not invent facts unsupported by the inputs
- Keep each list item to one clear sentence
- source: "text" for typed notes or metadata; "photo" for field/context photos or note photos;
  "voice" for items evident from voice memos
- Each item in findings must have type "finding", blockers type "blocker", follow_ups type "follow_up"
- Sentiment must reflect community mood, not the field worker's personal opinion alone"""

JSON_REPAIR_PROMPT = (
    "Your previous response was not valid JSON for the required schema. "
    "Return ONLY valid JSON matching the schema. No markdown fences or commentary."
)


def _require_api_key() -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    return settings.gemini_api_key


def _get_client() -> genai.Client:
    return genai.Client(api_key=_require_api_key())


def _gemini_error(exc: ClientError) -> RuntimeError:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return RuntimeError(
            "Gemini API quota exceeded. Wait a minute and retry — "
            "your debrief may already be ready if a prior request succeeded."
        )
    return RuntimeError(f"Gemini API error: {exc}")


def _clean_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove keys that can break Gemini schema validation."""
    cleaned: dict[str, Any] = {}
    for key, value in schema.items():
        if key in {"additionalProperties", "$schema", "title"}:
            continue
        if isinstance(value, dict):
            cleaned[key] = _clean_json_schema(value)
        elif isinstance(value, list):
            cleaned[key] = [
                _clean_json_schema(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def _parse_debrief_json(raw_text: str) -> DebriefResult:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(text)
    return DebriefResult.model_validate(data)


def _normalize_structured(
    structured: VisitStructuredInput | dict[str, str] | None,
) -> VisitStructuredInput | None:
    if structured is None:
        return None
    if isinstance(structured, VisitStructuredInput):
        return structured
    return VisitStructuredInput.model_validate(structured)


def _build_debrief_prompt(
    raw_notes: str,
    structured: VisitStructuredInput | None,
    *,
    has_photo_notes: bool,
    field_photo_count: int = 0,
    voice_memo_count: int = 0,
) -> str:
    sections: list[str] = []

    if structured:
        sections.append(
            "Structured visit data (form fields):\n"
            f"- Location: {structured.location}\n"
            f"- Visit date: {structured.visit_date}\n"
            f"- Program area: {structured.program_area}\n"
            f"- Stakeholders met: {structured.stakeholders}"
        )

    unstructured_label = "Unstructured field notes (text)"
    if has_photo_notes:
        unstructured_label += " — includes content transcribed from handwritten note photos"
    sections.append(f"{unstructured_label}:\n\n{raw_notes.strip()}")

    if field_photo_count:
        sections.append(
            f"Field context photos: {field_photo_count} image(s) attached above. "
            "Interpret them directly for location, people, proof of work, and conditions."
        )
    if voice_memo_count:
        sections.append(
            f"Voice memos: {voice_memo_count} recording(s) attached above. "
            "Interpret them directly — they were not converted to text."
        )

    sections.append(
        "Generate the four-section debrief: key findings, blockers observed, "
        "community sentiment, and suggested follow-ups."
    )
    return "\n\n".join(sections)


def _normalize_mime_for_gemini(mime_type: str) -> str:
    base = mime_type.split(";")[0].strip().lower()
    return MIME_ALIASES.get(base, base)


def _extract_response_text(response: Any) -> str:
    if response.text and response.text.strip():
        return response.text.strip()

    chunks: list[str] = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", None) or []:
            text = getattr(part, "text", None)
            if text and text.strip():
                chunks.append(text.strip())

    return "\n".join(chunks).strip()


def transcribe_image(
    image_bytes: bytes,
    *,
    mime_type: str = "image/jpeg",
    context: VisitStructuredInput | dict[str, str] | None = None,
    model: str | None = None,
    filename: str | None = None,
) -> str:
    client = _get_client()
    model = model or settings.gemini_model
    structured = _normalize_structured(context)

    resolved_mime = resolve_image_mime(
        image_bytes,
        filename=filename,
        declared=mime_type,
    )
    gemini_mime = _normalize_mime_for_gemini(resolved_mime)

    context_lines: list[str] = []
    if structured:
        context_lines = [
            f"Location: {structured.location}",
            f"Program area: {structured.program_area}",
            f"Stakeholders: {structured.stakeholders}",
            f"Visit date: {structured.visit_date}",
        ]
    context_block = "\n".join(context_lines)
    user_text = "Transcribe the handwritten notes in this image."
    if context_block:
        user_text = f"{user_text}\n\nStructured visit context:\n{context_block}"

    logger.info("Transcribing image with MIME %s (model=%s)", gemini_mime, model)

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=gemini_mime),
                user_text,
            ],
            config=types.GenerateContentConfig(
                system_instruction=TRANSCRIPTION_PROMPT,
                temperature=0.2,
            ),
        )
    except ClientError as exc:
        raise _gemini_error(exc) from exc
    text = _extract_response_text(response)
    if not text:
        finish = None
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            finish = getattr(candidates[0], "finish_reason", None)
        raise RuntimeError(
            f"Gemini returned an empty transcription (finish_reason={finish!r}, mime={gemini_mime})"
        )
    return text


def transcribe_audio(
    audio_bytes: bytes,
    *,
    mime_type: str = "audio/mpeg",
    context: VisitStructuredInput | dict[str, str] | None = None,
    model: str | None = None,
    filename: str | None = None,
) -> str:
    client = _get_client()
    model = model or settings.gemini_model
    structured = _normalize_structured(context)

    resolved_mime = resolve_audio_mime(
        audio_bytes,
        filename=filename,
        declared=mime_type,
    )
    gemini_mime = _normalize_mime_for_gemini(resolved_mime)
    if gemini_mime == "audio/mp3":
        gemini_mime = "audio/mpeg"

    context_lines: list[str] = []
    if structured:
        context_lines = [
            f"Location: {structured.location}",
            f"Program area: {structured.program_area}",
            f"Stakeholders: {structured.stakeholders}",
            f"Visit date: {structured.visit_date}",
        ]
    context_block = "\n".join(context_lines)
    user_text = "Transcribe the voice memo from this field visit."
    if context_block:
        user_text = f"{user_text}\n\nStructured visit context:\n{context_block}"

    logger.info("Transcribing audio with MIME %s (model=%s)", gemini_mime, model)

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=gemini_mime),
                user_text,
            ],
            config=types.GenerateContentConfig(
                system_instruction=VOICE_TRANSCRIPTION_PROMPT,
                temperature=0.2,
            ),
        )
    except ClientError as exc:
        raise _gemini_error(exc) from exc
    text = _extract_response_text(response)
    if not text:
        finish = None
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            finish = getattr(candidates[0], "finish_reason", None)
        raise RuntimeError(
            f"Gemini returned an empty transcription (finish_reason={finish!r}, mime={gemini_mime})"
        )
    return text


def _normalize_audio_mime_for_gemini(mime_type: str) -> str:
    base = _normalize_mime_for_gemini(mime_type)
    if base == "audio/mp3":
        return "audio/mpeg"
    return base


def generate_debrief(
    raw_notes: str,
    structured: VisitStructuredInput | dict[str, str] | None = None,
    *,
    has_photo_notes: bool = False,
    field_photos: list[tuple[bytes, str]] | None = None,
    voice_memos: list[tuple[bytes, str]] | None = None,
    model: str | None = None,
) -> DebriefResult:
    """
    Build debrief from text notes plus field photos and voice memos interpreted directly.
    """
    model = model or settings.gemini_model
    structured_input = _normalize_structured(structured)
    field_photos = field_photos or []
    voice_memos = voice_memos or []
    user_prompt = _build_debrief_prompt(
        raw_notes,
        structured_input,
        has_photo_notes=has_photo_notes,
        field_photo_count=len(field_photos),
        voice_memo_count=len(voice_memos),
    )

    schema = _clean_json_schema(DebriefResult.model_json_schema())
    client = _get_client()

    content_parts: list[Any] = []
    for idx, (image_bytes, mime_type) in enumerate(field_photos):
        resolved = resolve_image_mime(image_bytes, declared=mime_type)
        gemini_mime = _normalize_mime_for_gemini(resolved)
        content_parts.append(
            types.Part.from_bytes(data=image_bytes, mime_type=gemini_mime)
        )
        logger.info("Debrief field photo %s MIME %s", idx + 1, gemini_mime)

    for idx, (audio_bytes, mime_type) in enumerate(voice_memos):
        resolved = resolve_audio_mime(audio_bytes, declared=mime_type)
        gemini_mime = _normalize_audio_mime_for_gemini(resolved)
        content_parts.append(
            types.Part.from_bytes(data=audio_bytes, mime_type=gemini_mime)
        )
        logger.info("Debrief voice memo %s MIME %s", idx + 1, gemini_mime)

    content_parts.append(user_prompt)

    for attempt in range(2):
        prompt_text = user_prompt if attempt == 0 else f"{JSON_REPAIR_PROMPT}\n\n{user_prompt}"
        request_contents: Any = (
            [*content_parts[:-1], prompt_text]
            if content_parts[:-1]
            else prompt_text
        )
        try:
            response = client.models.generate_content(
                model=model,
                contents=request_contents,
                config=types.GenerateContentConfig(
                    system_instruction=DEBRIEF_SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
        except ClientError as exc:
            raise _gemini_error(exc) from exc
        raw = response.text or ""
        try:
            return _parse_debrief_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Debrief JSON parse failed (attempt %s): %s", attempt + 1, exc)
            if attempt == 1:
                raise RuntimeError("Gemini debrief response was not valid JSON") from exc

    raise RuntimeError("Failed to generate debrief")

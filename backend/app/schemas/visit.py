from pydantic import BaseModel, Field

from app.schemas.debrief import DebriefResult


class PreprocessVisitResponse(BaseModel):
    """Step 1 — session created; review raw_notes only when note images were transcribed."""

    session_id: str
    raw_notes: str = Field(description="Typed and/or transcribed free-form notes")
    needs_review: bool = Field(
        description="True when note images were transcribed — show edit screen before debrief",
    )


class DebriefResponse(BaseModel):
    """Step 2 — debrief preview linked to session for save."""

    session_id: str
    debrief: DebriefResult


class SaveVisitRequest(BaseModel):
    """Step 3 — persist confirmed visit after debrief review."""

    session_id: str
    raw_notes: str | None = Field(
        default=None,
        description="Optional final edit to notes before save",
    )
    debrief: DebriefResult = Field(description="Confirmed debrief (may be edited in UI)")


class SaveVisitResponse(BaseModel):
    visit_id: int
    message: str = "Visit saved successfully"

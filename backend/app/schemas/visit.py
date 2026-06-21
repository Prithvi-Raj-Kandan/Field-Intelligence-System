from datetime import date, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from app.schemas.debrief import DebriefItem, DebriefResult


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


class VisitSessionStatusResponse(BaseModel):
    """Workflow session state — used to recover debrief after transient API errors."""

    session_id: str
    status: str
    raw_notes: str
    debrief: DebriefResult | None = None


class VisitSummary(BaseModel):
    id: int
    location: str
    visit_date: date
    program_area: str
    sentiment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitListItem(VisitSummary):
    """Manager list row with blocker count and worker."""

    blocker_count: int = 0
    worker_name: str | None = None
    worker_email: str | None = None


class PaginatedVisitsResponse(BaseModel):
    items: list[VisitListItem]
    total: int
    page: int
    page_size: int


class FindingDetail(DebriefItem):
    id: int
    category: str | None = None


class ManagerVisitDetail(VisitSummary):
    """Manager drill-down with resolved media URLs."""

    stakeholders: str
    raw_notes: str
    note_image_paths: list[str] = Field(default_factory=list)
    field_photo_paths: list[str] = Field(default_factory=list)
    voice_memo_paths: list[str] = Field(default_factory=list)
    note_image_urls: list[str] = Field(default_factory=list)
    field_photo_urls: list[str] = Field(default_factory=list)
    voice_memo_urls: list[str] = Field(default_factory=list)
    findings: list[FindingDetail] = Field(default_factory=list)


class VisitDetail(VisitSummary):
    stakeholders: str
    raw_notes: str
    note_image_paths: list[str] = Field(default_factory=list)
    field_photo_paths: list[str] = Field(default_factory=list)
    voice_memo_paths: list[str] = Field(default_factory=list)
    findings: list[DebriefItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class GalleryMediaItem(BaseModel):
    visit_id: int
    path: str
    media_type: str = "field"
    location: str
    visit_date: date


class RecordingMediaItem(BaseModel):
    visit_id: int
    path: str
    location: str
    visit_date: date

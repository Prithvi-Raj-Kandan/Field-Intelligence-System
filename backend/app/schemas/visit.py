from datetime import date
from uuid import uuid4

from pydantic import BaseModel, Field


class DraftResponse(BaseModel):
    transcription: str
    note_image_path: str | None = None
    draft_id: str = Field(default_factory=lambda: str(uuid4()))

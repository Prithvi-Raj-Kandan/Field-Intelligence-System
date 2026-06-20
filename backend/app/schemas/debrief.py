from typing import Literal

from pydantic import BaseModel, Field


class VisitStructuredInput(BaseModel):
    """Structured visit fields entered by the field worker (form metadata)."""

    location: str
    visit_date: str
    program_area: str
    stakeholders: str


class DebriefItem(BaseModel):
    type: Literal["finding", "blocker", "follow_up"]
    text: str
    source: Literal["text", "photo", "voice"] = "text"


class DebriefResult(BaseModel):
    """
    AI debrief summary — four sections that power the manager analytics dashboard.

    UI label              | JSON field   | Saved to
    ----------------------|--------------|---------------------------
    Key findings          | findings     | findings (type=finding)
    Blockers observed     | blockers     | findings (type=blocker)
    Community sentiment   | sentiment    | visits.sentiment
    Suggested follow-ups  | follow_ups   | findings (type=follow_up)
    """

    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Community sentiment — overall mood from the visit",
    )
    findings: list[DebriefItem] = Field(
        default_factory=list,
        description="Key findings — observations, outcomes, community feedback",
    )
    blockers: list[DebriefItem] = Field(
        default_factory=list,
        description="Blockers observed — obstacles preventing program progress",
    )
    follow_ups: list[DebriefItem] = Field(
        default_factory=list,
        description="Suggested follow-ups — concrete next actions",
    )

    def all_items(self) -> list[DebriefItem]:
        """Flatten all debrief rows for persistence to the findings table."""
        return [*self.findings, *self.blockers, *self.follow_ups]

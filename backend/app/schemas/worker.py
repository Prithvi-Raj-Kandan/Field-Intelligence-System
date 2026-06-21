from datetime import date

from pydantic import BaseModel


class WorkerProfileItem(BaseModel):
    id: int
    name: str
    email: str
    visit_count: int
    negative_sentiment_pct: float
    most_common_blocker: str | None = None
    most_common_blocker_count: int = 0
    last_visit_date: date | None = None


class WorkerListResponse(BaseModel):
    items: list[WorkerProfileItem]

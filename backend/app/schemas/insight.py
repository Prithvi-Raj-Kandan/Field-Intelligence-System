from datetime import date, datetime

from pydantic import BaseModel, Field


class InsightFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    program_area: str | None = None
    location: str | None = None


class InsightSummaryResponse(BaseModel):
    total_visits: int
    negative_sentiment_pct: float = Field(description="Percentage of visits with negative sentiment")
    most_common_blocker: str | None = None
    most_common_blocker_count: int = 0


class BlockerInsightItem(BaseModel):
    group: str
    blocker_text: str
    count: int


class BlockerInsightsResponse(BaseModel):
    items: list[BlockerInsightItem]


class SentimentTrendItem(BaseModel):
    period: date
    positive: int
    neutral: int
    negative: int


class SentimentTrendResponse(BaseModel):
    items: list[SentimentTrendItem]

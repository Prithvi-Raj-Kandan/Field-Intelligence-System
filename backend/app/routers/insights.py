from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_role
from app.models.user import User
from app.schemas.insight import (
    BlockerInsightsResponse,
    InsightSummaryResponse,
    SentimentTrendResponse,
)
from app.services.insights import (
    get_blocker_insights,
    get_insight_summary,
    get_sentiment_trend,
)

router = APIRouter(prefix="/insights", tags=["insights"])

manager_required = require_role("manager")


@router.get("/summary", response_model=InsightSummaryResponse)
def insight_summary(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    program_area: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
) -> InsightSummaryResponse:
    """Dashboard headline metrics for filtered visits."""
    _ = current_user
    return get_insight_summary(
        db,
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
    )


@router.get("/blockers", response_model=BlockerInsightsResponse)
def insight_blockers(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    program_area: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    group_by: Annotated[
        Literal["location", "program_area", "text"],
        Query(description="Group blockers by visit location, program area, or blocker text"),
    ] = "location",
) -> BlockerInsightsResponse:
    """Recurring blockers aggregated across visits."""
    _ = current_user
    return get_blocker_insights(
        db,
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        group_by=group_by,
    )


@router.get("/sentiment-trend", response_model=SentimentTrendResponse)
def insight_sentiment_trend(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    program_area: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    interval: Annotated[
        Literal["day", "week"],
        Query(description="Bucket size for sentiment counts"),
    ] = "week",
) -> SentimentTrendResponse:
    """Sentiment counts over time (week buckets by default)."""
    _ = current_user
    return get_sentiment_trend(
        db,
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        interval=interval,
    )

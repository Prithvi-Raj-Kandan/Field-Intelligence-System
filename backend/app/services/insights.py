"""SQL aggregations for the manager dashboard."""

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.visit import Visit
from app.schemas.insight import (
    BlockerInsightItem,
    BlockerInsightsResponse,
    InsightSummaryResponse,
    SentimentTrendItem,
    SentimentTrendResponse,
)


def _visit_filters(
    *,
    date_from: date | None,
    date_to: date | None,
    program_area: str | None,
    location: str | None,
):
    clauses = []
    if date_from is not None:
        clauses.append(Visit.visit_date >= date_from)
    if date_to is not None:
        clauses.append(Visit.visit_date <= date_to)
    if program_area:
        clauses.append(Visit.program_area == program_area.strip())
    if location:
        clauses.append(Visit.location.ilike(f"%{location.strip()}%"))
    return clauses


def get_insight_summary(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
) -> InsightSummaryResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
    )

    total = db.scalar(select(func.count()).select_from(Visit).where(*filters)) or 0

    negative_count = 0
    if total > 0:
        negative_count = (
            db.scalar(
                select(func.count())
                .select_from(Visit)
                .where(*filters, Visit.sentiment == "negative")
            )
            or 0
        )

    negative_pct = round((negative_count / total) * 100, 1) if total else 0.0

    blocker_stmt = (
        select(Finding.text, func.count().label("cnt"))
        .join(Visit, Finding.visit_id == Visit.id)
        .where(Finding.type == "blocker", *filters)
        .group_by(Finding.text)
        .order_by(func.count().desc(), Finding.text)
        .limit(1)
    )
    top_blocker = db.execute(blocker_stmt).first()

    return InsightSummaryResponse(
        total_visits=total,
        negative_sentiment_pct=negative_pct,
        most_common_blocker=top_blocker.text if top_blocker else None,
        most_common_blocker_count=int(top_blocker.cnt) if top_blocker else 0,
    )


def get_blocker_insights(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    group_by: str = "location",
) -> BlockerInsightsResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
    )

    if group_by == "program_area":
        group_col = Visit.program_area
    elif group_by == "text":
        group_col = Finding.text
    else:
        group_by = "location"
        group_col = Visit.location

    stmt = (
        select(
            group_col.label("group"),
            Finding.text.label("blocker_text"),
            func.count().label("count"),
        )
        .join(Visit, Finding.visit_id == Visit.id)
        .where(Finding.type == "blocker", *filters)
        .group_by(group_col, Finding.text)
        .order_by(func.count().desc(), group_col, Finding.text)
    )

    rows = db.execute(stmt).all()
    items = [
        BlockerInsightItem(
            group=row.group,
            blocker_text=row.blocker_text,
            count=int(row.count),
        )
        for row in rows
    ]
    return BlockerInsightsResponse(items=items)


def get_sentiment_trend(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    interval: str = "week",
) -> SentimentTrendResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
    )

    if interval == "day":
        period_expr = Visit.visit_date
    else:
        interval = "week"
        period_expr = func.date_trunc("week", Visit.visit_date)

    stmt = (
        select(
            period_expr.label("period"),
            func.sum(case((Visit.sentiment == "positive", 1), else_=0)).label("positive"),
            func.sum(case((Visit.sentiment == "neutral", 1), else_=0)).label("neutral"),
            func.sum(case((Visit.sentiment == "negative", 1), else_=0)).label("negative"),
        )
        .where(*filters, Visit.sentiment.isnot(None))
        .group_by(period_expr)
        .order_by(period_expr)
    )

    items: list[SentimentTrendItem] = []
    for row in db.execute(stmt).all():
        period_value = row.period
        if hasattr(period_value, "date"):
            period_value = period_value.date()
        items.append(
            SentimentTrendItem(
                period=period_value,
                positive=int(row.positive or 0),
                neutral=int(row.neutral or 0),
                negative=int(row.negative or 0),
            )
        )

    return SentimentTrendResponse(items=items)

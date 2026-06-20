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
    RecurringBlockerItem,
    RecurringBlockersResponse,
    SentimentTrendItem,
    SentimentTrendResponse,
)


def _visit_filters(
    *,
    date_from: date | None,
    date_to: date | None,
    program_area: str | None,
    location: str | None,
    worker_id: int | None = None,
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
    if worker_id is not None:
        clauses.append(Visit.user_id == worker_id)
    return clauses


def _region_from_location(location: str) -> str:
    if " - " in location:
        return location.split(" - ", 1)[0].strip()
    return location.strip()


def get_insight_summary(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    worker_id: int | None = None,
) -> InsightSummaryResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
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
    worker_id: int | None = None,
    group_by: str = "location",
) -> BlockerInsightsResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
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


def get_recurring_blockers(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    worker_id: int | None = None,
) -> RecurringBlockersResponse:
    """Aggregate blockers by text across visits, with region linkage."""
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
    )

    stmt = (
        select(Finding.text, Visit.id, Visit.location)
        .join(Visit, Finding.visit_id == Visit.id)
        .where(Finding.type == "blocker", *filters)
    )

    aggregated: dict[str, dict[str, set]] = {}
    for text, visit_id, visit_location in db.execute(stmt).all():
        bucket = aggregated.setdefault(text, {"visit_ids": set(), "regions": set()})
        bucket["visit_ids"].add(visit_id)
        bucket["regions"].add(_region_from_location(visit_location))

    items = [
        RecurringBlockerItem(
            blocker_text=text,
            count=len(data["visit_ids"]),
            regions=sorted(data["regions"]),
        )
        for text, data in aggregated.items()
    ]
    items.sort(key=lambda item: (-item.count, item.blocker_text))
    return RecurringBlockersResponse(items=items)


def get_sentiment_trend(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    program_area: str | None = None,
    location: str | None = None,
    worker_id: int | None = None,
    interval: str = "week",
) -> SentimentTrendResponse:
    filters = _visit_filters(
        date_from=date_from,
        date_to=date_to,
        program_area=program_area,
        location=location,
        worker_id=worker_id,
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

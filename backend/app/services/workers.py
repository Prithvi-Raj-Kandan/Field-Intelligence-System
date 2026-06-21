"""Field worker profiles and stats for manager dashboard."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.user import User
from app.models.visit import Visit
from app.schemas.worker import WorkerListResponse, WorkerProfileItem


def list_workers_with_stats(db: Session) -> WorkerListResponse:
    workers = db.scalars(
        select(User).where(User.role == "field_worker").order_by(User.email)
    ).all()

    items: list[WorkerProfileItem] = []
    for worker in workers:
        visits = db.scalars(select(Visit).where(Visit.user_id == worker.id)).all()
        total = len(visits)
        negative_count = sum(1 for v in visits if v.sentiment == "negative")
        negative_pct = round((negative_count / total) * 100, 1) if total else 0.0

        last_visit = max((v.visit_date for v in visits), default=None)

        top_blocker = None
        top_count = 0
        if total > 0:
            blocker_stmt = (
                select(Finding.text, func.count().label("cnt"))
                .join(Visit, Finding.visit_id == Visit.id)
                .where(Finding.type == "blocker", Visit.user_id == worker.id)
                .group_by(Finding.text)
                .order_by(func.count().desc(), Finding.text)
                .limit(1)
            )
            row = db.execute(blocker_stmt).first()
            if row:
                top_blocker = row.text
                top_count = int(row.cnt)

        items.append(
            WorkerProfileItem(
                id=worker.id,
                name=worker.name,
                email=worker.email,
                visit_count=total,
                negative_sentiment_pct=negative_pct,
                most_common_blocker=top_blocker,
                most_common_blocker_count=top_count,
                last_visit_date=last_visit,
            )
        )

    return WorkerListResponse(items=items)

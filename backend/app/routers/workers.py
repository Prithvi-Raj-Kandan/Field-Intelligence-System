from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_role
from app.models.user import User
from app.schemas.worker import WorkerListResponse
from app.services.workers import list_workers_with_stats

router = APIRouter(prefix="/workers", tags=["workers"])

manager_required = require_role("manager")


@router.get("", response_model=WorkerListResponse)
def list_workers(
    current_user: Annotated[User, Depends(manager_required)],
    db: Annotated[Session, Depends(get_db)],
) -> WorkerListResponse:
    """Field worker profiles with visit analytics for manager view."""
    _ = current_user
    return list_workers_with_stats(db)

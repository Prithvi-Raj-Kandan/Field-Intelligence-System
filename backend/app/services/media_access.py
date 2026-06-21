"""Verify authenticated access to uploaded media files."""

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.visit import Visit
from app.models.visit_session import VisitSession


def _path_in_json(column, path: str):
    """PostgreSQL JSON array contains check (path is an element of the array)."""
    return column.cast(JSONB).contains([path])


def user_can_access_media(db: Session, user: User, relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if user.role == "manager":
        return _media_exists_on_any_visit(db, normalized) or _media_exists_on_session(
            db, normalized
        )

    visit_stmt = select(Visit.id).where(
        Visit.user_id == user.id,
        or_(
            _path_in_json(Visit.note_image_paths, normalized),
            _path_in_json(Visit.field_photo_paths, normalized),
            _path_in_json(Visit.voice_memo_paths, normalized),
        ),
    )
    if db.scalar(visit_stmt) is not None:
        return True

    session_stmt = select(VisitSession.session_id).where(
        VisitSession.user_id == user.id,
        or_(
            _path_in_json(VisitSession.note_image_paths, normalized),
            _path_in_json(VisitSession.field_photo_paths, normalized),
            _path_in_json(VisitSession.voice_memo_paths, normalized),
        ),
    )
    return db.scalar(session_stmt) is not None


def _media_exists_on_any_visit(db: Session, path: str) -> bool:
    stmt = select(Visit.id).where(
        or_(
            _path_in_json(Visit.note_image_paths, path),
            _path_in_json(Visit.field_photo_paths, path),
            _path_in_json(Visit.voice_memo_paths, path),
        ),
    )
    return db.scalar(stmt) is not None


def _media_exists_on_session(db: Session, path: str) -> bool:
    stmt = select(VisitSession.session_id).where(
        or_(
            _path_in_json(VisitSession.note_image_paths, path),
            _path_in_json(VisitSession.field_photo_paths, path),
            _path_in_json(VisitSession.voice_memo_paths, path),
        ),
    )
    return db.scalar(stmt) is not None

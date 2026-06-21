"""Shared SQLAlchemy engine factory (password URLs + RDS IAM auth tokens)."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL


def create_db_engine(*, poolclass=None, pool_pre_ping: bool = False) -> Engine:
    """Create engine from DATABASE_URL or RDS_IAM_TOKEN + RDS_* env vars."""
    iam_token = os.environ.get("RDS_IAM_TOKEN", "").strip()
    if iam_token:
        url = URL.create(
            drivername="postgresql",
            username=os.environ["RDS_USER"],
            host=os.environ["RDS_HOST"],
            port=int(os.environ.get("RDS_PORT", "5432")),
            database=os.environ.get("RDS_DB", "postgres"),
            query={"sslmode": "require"},
        )
        kwargs: dict = {"connect_args": {"password": iam_token}}
    else:
        from app.config import settings

        url = os.environ.get("DATABASE_URL") or settings.database_url
        kwargs = {}

    if poolclass is not None:
        kwargs["poolclass"] = poolclass
    if pool_pre_ping:
        kwargs["pool_pre_ping"] = True
    return create_engine(url, **kwargs)

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool

# Project root: backend/alembic/env.py -> parents[2]
_backend_dir = Path(__file__).resolve().parents[1]
_project_root = _backend_dir.parent
sys.path.insert(0, str(_backend_dir))

load_dotenv(_project_root / ".env.local")
load_dotenv(_project_root / ".env")

from app.config import settings  # noqa: E402
from app.database import Base  # noqa: E402
from app.db_connect import create_db_engine  # noqa: E402
from app.models import Finding, User, Visit, VisitSession  # noqa: F401, E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Prefer DATABASE_URL from environment (RDS migration) over .env.local."""
    if os.environ.get("RDS_IAM_TOKEN", "").strip():
        return "(RDS IAM auth via RDS_IAM_TOKEN env var)"
    return os.environ.get("DATABASE_URL") or settings.database_url


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_db_engine(poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

"""Seed demo users for local development."""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.services.auth import create_user, get_user_by_email

DEMO_WORKER_PASSWORD = os.environ.get("DEMO_WORKER_PASSWORD", "FieldIntel-Worker-2026!")
DEMO_MANAGER_PASSWORD = os.environ.get("DEMO_MANAGER_PASSWORD", "FieldIntel-Manager-2026!")

DEMO_USERS = [
    {
        "email": "worker@ngo.org",
        "password": DEMO_WORKER_PASSWORD,
        "role": "field_worker",
        "name": "Demo Field Worker",
    },
    {
        "email": "manager@ngo.org",
        "password": DEMO_MANAGER_PASSWORD,
        "role": "manager",
        "name": "Demo Manager",
    },
]


def seed_users() -> None:
    db = SessionLocal()
    try:
        for entry in DEMO_USERS:
            existing = get_user_by_email(db, entry["email"])
            if existing:
                print(f"Skip (exists): {entry['email']}")
                continue
            create_user(
                db,
                email=entry["email"],
                password=entry["password"],
                role=entry["role"],
                name=entry["name"],
            )
            print(f"Created: {entry['email']} ({entry['role']})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()

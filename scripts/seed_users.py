"""Seed demo users for local development."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal
from app.services.auth import create_user, get_user_by_email

DEMO_USERS = [
    {"email": "worker@ngo.org", "password": "demo1234", "role": "field_worker"},
    {"email": "manager@ngo.org", "password": "demo1234", "role": "manager"},
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
            )
            print(f"Created: {entry['email']} ({entry['role']})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()

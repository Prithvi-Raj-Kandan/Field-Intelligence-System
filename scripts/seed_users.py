"""Seed demo users for local development."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env.local")
load_dotenv(ROOT / ".env")

from app.database import SessionLocal
from app.services.auth import create_user, get_user_by_email, hash_password

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


def seed_users(*, force: bool = False) -> None:
    db = SessionLocal()
    try:
        for entry in DEMO_USERS:
            existing = get_user_by_email(db, entry["email"])
            if existing:
                if force:
                    existing.password_hash = hash_password(entry["password"])
                    existing.name = entry["name"]
                    existing.role = entry["role"]
                    db.commit()
                    print(f"Updated: {entry['email']} ({entry['role']})")
                else:
                    print(f"Skip (exists): {entry['email']} — run with --force to reset password")
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
    parser = argparse.ArgumentParser(description="Seed demo users")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reset demo user passwords and names from .env.local",
    )
    args = parser.parse_args()
    seed_users(force=args.force)

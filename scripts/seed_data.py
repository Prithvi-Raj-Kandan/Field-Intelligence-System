"""Seed demo visits with recurring blockers for manager dashboard testing.

Usage:
    python scripts/seed_data.py          # skip if seed visits already exist
    python scripts/seed_data.py --force  # delete prior seed visits and re-insert
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models.finding import Finding
from app.models.visit import Visit
from app.schemas.debrief import DebriefItem, DebriefResult
from app.services.auth import create_user, get_user_by_email

SEED_MARKER = "[seed-data]"

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
            if get_user_by_email(db, entry["email"]):
                continue
            create_user(
                db,
                email=entry["email"],
                password=entry["password"],
                role=entry["role"],
                name=entry["name"],
            )
    finally:
        db.close()


def _item(
    kind: str,
    text: str,
    source: str = "text",
) -> DebriefItem:
    return DebriefItem(type=kind, text=text, source=source)  # type: ignore[arg-type]


def _visit_specs() -> list[dict]:
    """10 visits across 5 locations, 4 program areas, recurring blocker themes."""
    irrigation = "Broken irrigation canal — primary channel damaged in three sections"
    land_dispute = "Land access dispute blocking expansion of farmer cooperative plots"
    fund_delay = "Delayed fund disbursement from district office holding up program work"

    return [
        {
            "location": "Region Y - Village A",
            "visit_date": date(2026, 4, 8),
            "program_area": "Water Access",
            "stakeholders": "Village council, farmer cooperative",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "Irrigation channel serves 120 farming households."),
                    _item("finding", "Community is engaged and requesting engineering assessment."),
                ],
                blockers=[_item("blocker", irrigation)],
                follow_ups=[_item("follow_up", "Schedule engineering visit within two weeks.")],
            ),
        },
        {
            "location": "Region Y - Village B",
            "visit_date": date(2026, 4, 15),
            "program_area": "Water Access",
            "stakeholders": "Village council, women's SHG",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "Canal breach has worsened since last monsoon."),
                    _item("finding", "Women's group willing to co-manage water user committee."),
                ],
                blockers=[_item("blocker", irrigation)],
                follow_ups=[_item("follow_up", "Share Region Y canal repair cost estimate with council.")],
            ),
        },
        {
            "location": "Region Y - Village C",
            "visit_date": date(2026, 4, 22),
            "program_area": "Water Access",
            "stakeholders": "Block development officer, village council",
            "sentiment": "neutral",
            "debrief": DebriefResult(
                sentiment="neutral",
                findings=[
                    _item("finding", "Temporary pipe arrangement keeping minimal flow to fields."),
                ],
                blockers=[
                    _item("blocker", irrigation),
                    _item("blocker", fund_delay),
                ],
                follow_ups=[_item("follow_up", "Follow up with BDO on pending sanction letter.")],
            ),
        },
        {
            "location": "Region Y - Ward 5",
            "visit_date": date(2026, 5, 3),
            "program_area": "Water Access",
            "stakeholders": "Ward councillor, water user group",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "Farmers reporting 40% yield drop on downstream plots."),
                ],
                blockers=[_item("blocker", irrigation)],
                follow_ups=[_item("follow_up", "Prioritize Ward 5 for next repair tranche.")],
            ),
        },
        {
            "location": "Region Y - Block 2",
            "visit_date": date(2026, 5, 10),
            "program_area": "Water Access",
            "stakeholders": "District irrigation department liaison",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "Department acknowledged damage but cited budget cycle delay."),
                ],
                blockers=[
                    _item("blocker", irrigation),
                    _item("blocker", fund_delay),
                ],
                follow_ups=[_item("follow_up", "Escalate fund release with program director.")],
            ),
        },
        {
            "location": "Region X - Farm Cluster",
            "visit_date": date(2026, 4, 18),
            "program_area": "Agriculture",
            "stakeholders": "Farmer producer organization",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "50 members ready for drip irrigation training."),
                ],
                blockers=[_item("blocker", land_dispute)],
                follow_ups=[_item("follow_up", "Legal review of land records with district office.")],
            ),
        },
        {
            "location": "Region X - Village North",
            "visit_date": date(2026, 5, 6),
            "program_area": "Agriculture",
            "stakeholders": "Village council, FPO board",
            "sentiment": "neutral",
            "debrief": DebriefResult(
                sentiment="neutral",
                findings=[
                    _item("finding", "Pilot plot soil testing completed with positive results."),
                ],
                blockers=[_item("blocker", land_dispute)],
                follow_ups=[_item("follow_up", "Mediation session with disputed parcel owners.")],
            ),
        },
        {
            "location": "Hyderabad - Govt School Ward 12",
            "visit_date": date(2026, 5, 20),
            "program_area": "Education",
            "stakeholders": "Department of School Education, head teacher",
            "sentiment": "negative",
            "debrief": DebriefResult(
                sentiment="negative",
                findings=[
                    _item("finding", "150 students; outdoor classes due to classroom shortage."),
                ],
                blockers=[
                    _item("blocker", "Significant lack of digital infrastructure including smart boards."),
                    _item("blocker", fund_delay),
                ],
                follow_ups=[_item("follow_up", "Support July 1st fundraising event for lab equipment.")],
            ),
        },
        {
            "location": "Tumkur - Govt School Block 3",
            "visit_date": date(2026, 5, 28),
            "program_area": "Education",
            "stakeholders": "Block education officer, parent committee",
            "sentiment": "neutral",
            "debrief": DebriefResult(
                sentiment="neutral",
                findings=[
                    _item("finding", "Midday meal program running but sponsor slot vacant."),
                ],
                blockers=[
                    _item("blocker", "Government funds allocated for development not yet released."),
                ],
                follow_ups=[_item("follow_up", "Secure midday meal sponsor before next term.")],
            ),
        },
        {
            "location": "Bengaluru Urban - Slum Pocket 7",
            "visit_date": date(2026, 6, 5),
            "program_area": "Livelihoods",
            "stakeholders": "Self-help group leaders, municipal ward office",
            "sentiment": "positive",
            "debrief": DebriefResult(
                sentiment="positive",
                findings=[
                    _item("finding", "12 women completed tailoring certification; 8 already receiving orders."),
                    _item("finding", "Community mood upbeat after first market stall weekend."),
                ],
                blockers=[_item("blocker", fund_delay)],
                follow_ups=[_item("follow_up", "Link graduates to urban vendor licensing support.")],
            ),
        },
    ]


def _seed_notes(body: str) -> str:
    return f"{SEED_MARKER}\n{body.strip()}"


def has_seed_visits(db) -> bool:
    count = db.scalar(
        select(func.count())
        .select_from(Visit)
        .where(Visit.raw_notes.like(f"{SEED_MARKER}%"))
    )
    return bool(count and count > 0)


def clear_seed_visits(db) -> int:
    visits = db.scalars(
        select(Visit).where(Visit.raw_notes.like(f"{SEED_MARKER}%"))
    ).all()
    removed = len(visits)
    for visit in visits:
        db.delete(visit)
    if removed:
        db.commit()
    return removed


def _persist_visit(db, *, user_id: int, spec: dict) -> Visit:
    debrief: DebriefResult = spec["debrief"]
    notes = _seed_notes(
        f"Field notes for {spec['location']} on {spec['visit_date']}. "
        "Synthetic visit inserted by seed_data.py for dashboard demos."
    )
    visit = Visit(
        user_id=user_id,
        location=spec["location"],
        visit_date=spec["visit_date"],
        program_area=spec["program_area"],
        stakeholders=spec["stakeholders"],
        raw_notes=notes,
        note_image_paths=[],
        field_photo_paths=[],
        voice_memo_paths=[],
        sentiment=debrief.sentiment,
    )
    db.add(visit)
    db.flush()

    for item in debrief.all_items():
        db.add(
            Finding(
                visit_id=visit.id,
                type=item.type,
                text=item.text,
                source=item.source,
            )
        )

    db.commit()
    db.refresh(visit)
    return visit


def seed_visits(*, force: bool = False) -> None:
    seed_users()

    db = SessionLocal()
    try:
        worker = get_user_by_email(db, "worker@ngo.org")
        if worker is None:
            raise RuntimeError("worker@ngo.org not found — run seed_users.py first")

        if has_seed_visits(db):
            if not force:
                print("Seed visits already present — skipping (use --force to replace)")
                return
            removed = clear_seed_visits(db)
            print(f"Removed {removed} existing seed visit(s)")

        for spec in _visit_specs():
            visit = _persist_visit(db, user_id=worker.id, spec=spec)
            print(f"Created visit {visit.id}: {visit.location} ({visit.program_area})")

        print(f"\nDone — inserted {len(_visit_specs())} seed visits.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo visits for dashboard analytics")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing seed visits and re-insert",
    )
    args = parser.parse_args()
    seed_visits(force=args.force)


if __name__ == "__main__":
    main()

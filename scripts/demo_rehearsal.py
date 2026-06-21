"""S0213 — Full local E2E demo rehearsal (automated API checks + manual browser checklist).

Usage (from repo root, Postgres running):
    python scripts/demo_rehearsal.py
    python scripts/demo_rehearsal.py --with-gemini   # also run live debrief (uses API quota)
    python scripts/demo_rehearsal.py --live http://127.0.0.1:8000  # hit running uvicorn
"""

from __future__ import annotations

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

DEMO_WORKER_PASSWORD = os.environ.get("DEMO_WORKER_PASSWORD", "FieldIntel-Worker-2026!")
DEMO_MANAGER_PASSWORD = os.environ.get("DEMO_MANAGER_PASSWORD", "FieldIntel-Manager-2026!")


def _header(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def _ok(msg: str) -> None:
    print(f"  OK  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    raise SystemExit(1)


def _login(client, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    if response.status_code != 200:
        _fail(f"Login failed for {email}: {response.status_code} {response.text}")
    body = response.json()
    token = body.get("access_token")
    if not token:
        _fail(f"No access_token for {email}")
    return token


def run_api_checks(client, *, with_gemini: bool) -> None:
    _header("1. Auth")
    worker_token = _login(client, "worker@ngo.org", DEMO_WORKER_PASSWORD)
    manager_token = _login(client, "manager@ngo.org", DEMO_MANAGER_PASSWORD)
    _ok("Worker and manager login")

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {worker_token}"})
    if me.status_code != 200:
        _fail(f"GET /auth/me: {me.status_code}")
    _ok(f"Worker profile: {me.json().get('email')} ({me.json().get('name')})")

    _header("2. Manager dashboard data (seed)")
    headers = {"Authorization": f"Bearer {manager_token}"}

    summary = client.get("/insights/summary", headers=headers)
    if summary.status_code != 200:
        _fail(f"GET /insights/summary: {summary.status_code} {summary.text}")
    s = summary.json()
    _ok(f"Summary: {s['total_visits']} visits, {s['negative_sentiment_pct']}% negative")

    if s["total_visits"] < 5:
        print("  WARN  Few visits in DB — run: python scripts/seed_data.py --force")

    recurring = client.get(
        "/insights/recurring-blockers?program_area=Water+Access",
        headers=headers,
    )
    if recurring.status_code != 200:
        _fail(f"GET /insights/recurring-blockers: {recurring.status_code}")
    items = recurring.json().get("items", [])
    _ok(f"Recurring blockers: {len(items)} themes")
    if items:
        top = items[0]
        print(f"       Top blocker: {top['blocker_text'][:60]}... ({top['count']} visits)")

    trend = client.get("/insights/sentiment-trend", headers=headers)
    if trend.status_code != 200:
        _fail(f"GET /insights/sentiment-trend: {trend.status_code}")
    _ok(f"Sentiment trend: {len(trend.json().get('items', []))} points")

    blockers = client.get("/insights/blockers?group_by=location", headers=headers)
    if blockers.status_code != 200:
        _fail(f"GET /insights/blockers: {blockers.status_code}")
    _ok("Blockers by region")

    _header("3. Manager visits + CSV export")
    listing = client.get(
        "/visits?program_area=Water+Access&location=Region+Y+-+Village+A&page_size=5",
        headers=headers,
    )
    if listing.status_code != 200:
        _fail(f"GET /visits: {listing.status_code}")
    visits = listing.json()
    _ok(f"Filtered visits: {visits['total']} total")

    csv_res = client.get("/visits/export.csv?program_area=Water+Access", headers=headers)
    if csv_res.status_code != 200:
        _fail(f"GET /visits/export.csv: {csv_res.status_code}")
    if "text/csv" not in csv_res.headers.get("content-type", ""):
        _fail("CSV export wrong content-type")
    _ok(f"CSV export: {len(csv_res.text.splitlines())} lines")

    if visits["items"]:
        visit_id = visits["items"][0]["id"]
        detail = client.get(f"/visits/{visit_id}", headers=headers)
        if detail.status_code != 200:
            _fail(f"GET /visits/{visit_id}: {detail.status_code}")
        _ok(f"Visit detail #{visit_id} with {len(detail.json().get('findings', []))} findings")

    _header("4. Worker visit list + recordings")
    w_headers = {"Authorization": f"Bearer {worker_token}"}
    mine = client.get("/visits/mine", headers=w_headers)
    if mine.status_code != 200:
        _fail(f"GET /visits/mine: {mine.status_code}")
    _ok(f"Worker visits: {len(mine.json())}")

    recordings = client.get("/visits/mine/recordings", headers=w_headers)
    if recordings.status_code != 200:
        _fail(f"GET /visits/mine/recordings: {recordings.status_code}")
    _ok(f"Recordings index: {len(recordings.json())} items")

    gallery = client.get("/visits/mine/gallery", headers=w_headers)
    if gallery.status_code != 200:
        _fail(f"GET /visits/mine/gallery: {gallery.status_code}")
    _ok(f"Gallery index: {len(gallery.json())} items")

    _header(
        "5. Worker workflow (preprocess -> save, no Gemini)"
        if not with_gemini
        else "5. Full worker workflow (Gemini debrief)"
    )
    preprocess = client.post(
        "/visits/preprocess",
        headers=w_headers,
        data={
            "location": "Region Y - Village A",
            "visit_date": "2026-06-20",
            "program_area": "Water Access",
            "stakeholders": "Village council",
            "raw_notes": "Demo rehearsal visit — canal damage noted in section 2.",
        },
    )
    if preprocess.status_code != 200:
        _fail(f"POST /visits/preprocess: {preprocess.status_code} {preprocess.text}")
    session_id = preprocess.json()["session_id"]
    _ok(f"Preprocess session: {session_id}")

    if not with_gemini:
        print("  SKIP  Live debrief (pass --with-gemini to test Gemini)")
        return

    if not os.environ.get("GEMINI_DEBRIEF_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("  SKIP  No GEMINI_DEBRIEF_API_KEY / GEMINI_API_KEY set")
        return

    debrief = client.post(
        "/visits/debrief",
        headers=w_headers,
        data={"session_id": session_id},
    )
    if debrief.status_code != 200:
        _fail(f"POST /visits/debrief: {debrief.status_code} {debrief.text}")
    debrief_body = debrief.json()["debrief"]
    _ok(f"Debrief sentiment: {debrief_body['sentiment']}")

    save = client.post(
        "/visits/save",
        headers=w_headers,
        json={"session_id": session_id, "debrief": debrief_body},
    )
    if save.status_code != 201:
        _fail(f"POST /visits/save: {save.status_code} {save.text}")
    _ok(f"Saved visit #{save.json()['visit_id']}")


def print_manual_checklist() -> None:
    _header("Manual browser checklist (Section 13 demo)")
    print(
        """
  Prerequisites:
    - docker compose up -d
    - cd backend && .venv\\Scripts\\activate && uvicorn app.main:app --reload
    - cd frontend && npm run dev
    - python scripts/seed_users.py --force && python scripts/seed_data.py --force  (if dashboard looks empty)

  Credentials (.env.local):
    worker@ngo.org  / DEMO_WORKER_PASSWORD
    manager@ngo.org / DEMO_MANAGER_PASSWORD

  Step 1 - Field worker (http://localhost:5173)
    [ ] Landing page loads (new design)
    [ ] Sign in as worker
    [ ] Log visit: Region Y - Village A, Water Access, Village council
    [ ] Add free-form notes + optional note photo / voice memo
    [ ] Generate debrief -> review cards -> save
    [ ] Previous visits, Gallery, Recordings show saved media

  Step 2 - Manager
    [ ] Sign out -> sign in as manager
    [ ] Dashboard: filter Program "Water Access", Location "Region Y"
    [ ] Metric cards show negative sentiment %
    [ ] Recurring blockers: "Broken irrigation canal" with multiple visits
    [ ] Sentiment trend chart renders
    [ ] Visits page -> open visit drawer -> photos/audio load
    [ ] Export visits CSV downloads

  Step 3 - Console
    [ ] No red errors in browser DevTools during the flow

  Architecture talking points: see docs/deployment-vercel-aws.md
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="S0213 local demo rehearsal")
    parser.add_argument("--with-gemini", action="store_true", help="Run live debrief (uses Gemini quota)")
    parser.add_argument("--live", metavar="URL", help="Use httpx against running server instead of TestClient")
    args = parser.parse_args()

    _header("S0213 - Local E2E Demo Rehearsal")
    print(f"  Worker password: {'*' * len(DEMO_WORKER_PASSWORD)}")
    print(f"  Manager password: {'*' * len(DEMO_MANAGER_PASSWORD)}")

    if args.live:
        import httpx

        base = args.live.rstrip("/")
        client = httpx.Client(base_url=base, timeout=120.0)
        health = client.get("/health")
        if health.status_code != 200:
            _fail(f"GET /health on {base}: {health.status_code}")
        _ok(f"Live API health: {base}")

        class Adapter:
            def get(self, path, **kw):
                return client.get(path, **kw)

            def post(self, path, **kw):
                return client.post(path, **kw)

        run_api_checks(Adapter(), with_gemini=args.with_gemini)
    else:
        from fastapi.testclient import TestClient

        from app.main import app

        run_api_checks(TestClient(app), with_gemini=args.with_gemini)

    print_manual_checklist()
    _header("S0213 automated checks PASSED")
    print("  Complete the manual browser checklist above, then proceed to Stage 3 deployment.\n")


if __name__ == "__main__":
    main()

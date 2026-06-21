"""Smoke test for manager insight endpoints."""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def main() -> None:
    client = TestClient(app)

    worker_token = _login(client, "worker@ngo.org", os.environ.get("DEMO_WORKER_PASSWORD", "FieldIntel-Worker-2026!"))
    manager_token = _login(client, "manager@ngo.org", os.environ.get("DEMO_MANAGER_PASSWORD", "FieldIntel-Manager-2026!"))

    worker_res = client.get("/insights/summary", headers={"Authorization": f"Bearer {worker_token}"})
    assert worker_res.status_code == 403, worker_res.text

    headers = {"Authorization": f"Bearer {manager_token}"}

    summary = client.get("/insights/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert "total_visits" in body
    assert "negative_sentiment_pct" in body

    blockers = client.get("/insights/blockers?group_by=location", headers=headers)
    assert blockers.status_code == 200, blockers.text
    assert "items" in blockers.json()

    trend = client.get("/insights/sentiment-trend", headers=headers)
    assert trend.status_code == 200, trend.text
    assert "items" in trend.json()

    print("Insight endpoints: OK")
    print("Summary:", body)


if __name__ == "__main__":
    main()

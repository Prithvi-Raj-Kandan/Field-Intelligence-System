"""Smoke test for POST /visits/preprocess (step 1)."""

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
    token = _login(client, "worker@ngo.org", "demo1234")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/visits/preprocess",
        headers=headers,
        data={
            "location": "Region Y - Village A",
            "visit_date": "2026-06-18",
            "program_area": "Water Access",
            "stakeholders": "Village council",
            "raw_notes": "Canal damaged in three places. Community frustrated.",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["session_id"]
    assert "Canal damaged" in data["raw_notes"]
    assert data["needs_review"] is False
    print("Typed-notes preprocess: OK (needs_review=false)")

    empty = client.post(
        "/visits/preprocess",
        headers=headers,
        data={
            "location": "Region X",
            "visit_date": "2026-06-18",
            "program_area": "Agriculture",
            "stakeholders": "Co-op",
        },
    )
    assert empty.status_code == 400
    print("Empty input validation: OK")

    print("\nPOST /visits/preprocess tests passed")


if __name__ == "__main__":
    main()

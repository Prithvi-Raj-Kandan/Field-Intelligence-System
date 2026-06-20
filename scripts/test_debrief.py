"""Smoke test for POST /visits/debrief (requires session from preprocess)."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app

SAMPLE_NOTES = """
Met with village council. Irrigation canal damaged in three sections.
Community frustrated but engaged. Council requested engineering visit within two weeks.
"""


def _login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"email": "worker@ngo.org", "password": "demo1234"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def main() -> None:
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_login(client)}"}

    prep = client.post(
        "/visits/preprocess",
        headers=headers,
        data={
            "location": "Region Y - Village A",
            "visit_date": "2026-06-18",
            "program_area": "Water Access",
            "stakeholders": "Village council, farmer cooperative",
            "raw_notes": SAMPLE_NOTES,
        },
    ).json()

    response = client.post(
        "/visits/debrief",
        headers=headers,
        data={"session_id": prep["session_id"]},
    )
    assert response.status_code == 200, response.text
    data = response.json()["debrief"]

    assert data["sentiment"] in {"positive", "neutral", "negative"}
    assert data["findings"]
    assert data["blockers"]
    assert isinstance(data["follow_ups"], list)

    print("Sentiment:", data["sentiment"])
    print("Findings:", len(data["findings"]))
    print("Blockers:", len(data["blockers"]))
    print("Follow-ups:", len(data["follow_ups"]))
    print("\nPOST /visits/debrief test passed")


if __name__ == "__main__":
    main()

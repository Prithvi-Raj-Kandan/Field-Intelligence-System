"""Full workflow: preprocess -> debrief -> save (session-linked)."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app

SAMPLE_NOTES = """
Met with village council in Region Y - Village A regarding Water Access program.
Irrigation canal damaged in three sections. Community frustrated but engaged.
Women's group wants training before monsoon. Council requested engineering visit within two weeks.
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

    preprocess = client.post(
        "/visits/preprocess",
        headers=headers,
        data={
            "location": "Region Y - Village A",
            "visit_date": "2026-06-18",
            "program_area": "Water Access",
            "stakeholders": "Village council",
            "raw_notes": SAMPLE_NOTES,
        },
    )
    assert preprocess.status_code == 200, preprocess.text
    prep = preprocess.json()
    session_id = prep["session_id"]
    assert prep["needs_review"] is False

    edited_notes = prep["raw_notes"] + "\n\n[Worker edit] Confirmed damage at sections 2, 4, 7."

    debrief = client.post(
        "/visits/debrief",
        headers=headers,
        data={
            "session_id": session_id,
            "raw_notes": edited_notes,
        },
    )
    assert debrief.status_code == 200, debrief.text
    debrief_data = debrief.json()
    assert debrief_data["session_id"] == session_id
    debrief_body = debrief_data["debrief"]
    assert debrief_body["sentiment"] in {"positive", "neutral", "negative"}

    save = client.post(
        "/visits/save",
        headers=headers,
        json={
            "session_id": session_id,
            "raw_notes": edited_notes,
            "debrief": debrief_body,
        },
    )
    assert save.status_code == 201, save.text
    visit_id = save.json()["visit_id"]
    assert visit_id > 0

    duplicate = client.post(
        "/visits/save",
        headers=headers,
        json={"session_id": session_id, "debrief": debrief_body},
    )
    assert duplicate.status_code == 409

    print("Preprocess -> debrief -> save flow: OK")
    print("Visit ID:", visit_id)


if __name__ == "__main__":
    main()

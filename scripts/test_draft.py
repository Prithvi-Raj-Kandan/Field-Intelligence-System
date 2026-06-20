"""Smoke test for POST /visits/draft (S0107). Requires GEMINI_API_KEY for image path."""

import io
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.main import app

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def main() -> None:
    client = TestClient(app)
    token = _login(client, "worker@ngo.org", "demo1234")
    headers = {"Authorization": f"Bearer {token}"}

    # Text-only draft
    text_response = client.post(
        "/visits/draft",
        headers=headers,
        data={
            "location": "Region Y - Village A",
            "visit_date": "2026-06-18",
            "program_area": "Water Access",
            "stakeholders": "Village council",
            "raw_notes": "Canal damaged in three places. Community frustrated.",
        },
    )
    assert text_response.status_code == 200, text_response.text
    text_data = text_response.json()
    assert "Canal damaged" in text_data["transcription"]
    assert text_data["note_image_path"] is None
    print("Text-only draft: OK")

    # Manager should be forbidden
    manager_token = _login(client, "manager@ngo.org", "demo1234")
    forbidden = client.post(
        "/visits/draft",
        headers={"Authorization": f"Bearer {manager_token}"},
        data={
            "location": "Region X",
            "visit_date": "2026-06-18",
            "program_area": "Agriculture",
            "stakeholders": "Co-op",
            "raw_notes": "Test",
        },
    )
    assert forbidden.status_code == 403
    print("Role guard: OK")

    print("\nS0107 draft endpoint tests passed (text-only path)")
    print("To test photo transcription, use Swagger /docs with a real handwritten note image.")


if __name__ == "__main__":
    main()

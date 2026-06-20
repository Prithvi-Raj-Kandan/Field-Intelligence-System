"""Smoke test for manager GET /visits list + detail (S0202)."""

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

    worker_token = _login(client, "worker@ngo.org", "demo1234")
    manager_token = _login(client, "manager@ngo.org", "demo1234")

    worker_list = client.get("/visits", headers={"Authorization": f"Bearer {worker_token}"})
    assert worker_list.status_code == 403, worker_list.text

    headers = {"Authorization": f"Bearer {manager_token}"}

    listing = client.get("/visits?page=1&page_size=5", headers=headers)
    assert listing.status_code == 200, listing.text
    data = listing.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 5

    if data["items"]:
        item = data["items"][0]
        assert "blocker_count" in item
        visit_id = item["id"]

        detail = client.get(f"/visits/{visit_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        body = detail.json()
        assert body["id"] == visit_id
        assert "findings" in body
        assert "field_photo_urls" in body
        if body["field_photo_paths"]:
            assert body["field_photo_urls"][0].startswith("http")
            assert "/media/" in body["field_photo_urls"][0]

    filtered = client.get(
        "/visits?program_area=Education&location=Hyderabad",
        headers=headers,
    )
    assert filtered.status_code == 200, filtered.text

    missing = client.get("/visits/999999", headers=headers)
    assert missing.status_code == 404

    print("Manager visit list + detail: OK")
    print(f"Total visits: {data['total']}")


if __name__ == "__main__":
    main()

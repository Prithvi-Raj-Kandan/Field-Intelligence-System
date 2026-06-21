"""Smoke test for file storage (local or S3)."""

import io
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR.parent / ".env.local")

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.main import app
from app.storage import get_storage_backend

# Minimal 1x1 PNG
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

DEMO_WORKER_PASSWORD = os.environ.get("DEMO_WORKER_PASSWORD", "FieldIntel-Worker-2026!")


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": "worker@ngo.org", "password": DEMO_WORKER_PASSWORD},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def run_storage_test() -> None:
    storage = get_storage_backend()
    upload = UploadFile(
        filename="test.png",
        file=io.BytesIO(PNG_BYTES),
        headers={"content-type": "image/png"},
    )
    path = await storage.save(upload, folder="images")
    print(f"Saved: {path}")

    url = await storage.get_url(path)
    client = TestClient(app)
    response = client.get(url, headers=_auth_headers(client))
    if response.status_code == 403:
        print("  NOTE  Media 403 without visit link — upload/delete still OK for storage smoke test")
    elif response.status_code == 200:
        assert response.content == PNG_BYTES
        print(f"Served via {url}: OK")
    else:
        assert response.status_code == 200, response.text

    await storage.delete(path)
    assert not storage.exists(path)
    print("Delete: OK")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_storage_test())
    print("Storage test passed")

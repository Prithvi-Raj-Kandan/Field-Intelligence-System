"""Smoke test for local file storage (S0105)."""

import io
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

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
    response = client.get(url)
    assert response.status_code == 200, response.text
    assert response.content == PNG_BYTES
    print(f"Served via {url}: OK")

    await storage.delete(path)
    assert not (storage.upload_root / path).exists()
    print("Delete: OK")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_storage_test())
    print("S0105 storage test passed")

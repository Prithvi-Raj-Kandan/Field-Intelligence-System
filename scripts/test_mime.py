"""Tests for image MIME detection."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.utils.image_mime import resolve_image_mime

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 12
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


def main() -> None:
    assert resolve_image_mime(JPEG, declared="application/octet-stream") == "image/jpeg"
    assert resolve_image_mime(JPEG, declared="image/jpg") == "image/jpeg"
    assert resolve_image_mime(JPEG, filename="notes.JPG") == "image/jpeg"
    assert resolve_image_mime(PNG, declared=None, filename="scan.png") == "image/png"
    print("MIME detection tests passed")


if __name__ == "__main__":
    main()

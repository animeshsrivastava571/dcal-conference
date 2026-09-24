"""Fetch and extract the ConvFinQA release archive."""

from __future__ import annotations

import zipfile
from pathlib import Path

import requests

from handoff.config import DATA_DIR

ARCHIVE_URL = "https://raw.githubusercontent.com/czyssrs/ConvFinQA/main/data.zip"
ARCHIVE_BYTES = 17_512_756


def download(dest_dir: Path = DATA_DIR, force: bool = False) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / "data.zip"

    if force or not archive.exists():
        with requests.get(ARCHIVE_URL, stream=True, timeout=120) as response:
            response.raise_for_status()
            with archive.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)

    size = archive.stat().st_size
    if size != ARCHIVE_BYTES:
        raise RuntimeError(
            f"{archive} is {size} bytes, expected {ARCHIVE_BYTES}. "
            "Upstream data moved; the coverage figures in docs/01 no longer apply."
        )

    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest_dir)

    return dest_dir


if __name__ == "__main__":
    out = download()
    for path in sorted(out.rglob("*.json")):
        print(f"{path.stat().st_size:>12,}  {path.relative_to(out)}")

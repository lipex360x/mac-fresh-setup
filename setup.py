#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "questionary>=2.0",
#     "rich>=13.7",
# ]
# ///
"""Bootstrap for mac-fresh-setup.

Downloads the repository tarball at the configured ref (default: `main`),
extracts it to a temp directory, imports the `mac_fresh_setup` package and
runs the interactive menu. The temp directory is removed on exit.

Override the ref with `MAC_FRESH_SETUP_REF` (e.g. a tag like `v0.2.0`).
"""

from __future__ import annotations

import atexit
import io
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

REPO = "lipex360x/mac-fresh-setup"
DEFAULT_REF = "main"


def _fetch_tarball(ref: str) -> Path:
    url = f"https://codeload.github.com/{REPO}/tar.gz/{ref}"
    request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(request) as response:
        data = response.read()

    tmpdir = Path(tempfile.mkdtemp(prefix="mac-fresh-setup-"))
    atexit.register(shutil.rmtree, tmpdir, ignore_errors=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        archive.extractall(tmpdir)

    extracted = [p for p in tmpdir.iterdir() if p.is_dir()]
    if not extracted:
        raise RuntimeError(f"Tarball at {url} contained no top-level directory.")
    return extracted[0]


def main() -> None:
    ref = os.environ.get("MAC_FRESH_SETUP_REF", DEFAULT_REF)
    root = _fetch_tarball(ref)
    src_dir = root / "src"
    if not src_dir.is_dir():
        raise RuntimeError(f"Expected `src/` inside the tarball, got: {list(root.iterdir())}")
    sys.path.insert(0, str(src_dir))
    from app import run

    run()


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import subprocess
from typing import Any

from console import console


def safe_mode() -> bool:
    return os.environ.get("MAC_FRESH_SETUP_SAFE") == "1"


def mutating_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    if safe_mode():
        rendered = " ".join(str(part) for part in cmd)
        console.print(f"[red]SAFE MODE blocked mutating command:[/red] {rendered}")
        raise SystemExit(1)
    return subprocess.run(cmd, **kwargs)


def mutating_check(description: str) -> None:
    if safe_mode():
        console.print(f"[red]SAFE MODE blocked:[/red] {description}")
        raise SystemExit(1)

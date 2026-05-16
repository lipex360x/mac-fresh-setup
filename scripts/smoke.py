"""Local smoke test for mac-fresh-setup modules.

Runs every module function with `runtime.dry_run = True` AND
`MAC_FRESH_SETUP_SAFE=1` set, after monkey-patching `subprocess.run`
to a recording stub. Guarantees zero side effects on the host while
exercising every code path under safe defaults.

Usage:

    uv run --with questionary --with rich python scripts/smoke.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

os.environ["MAC_FRESH_SETUP_SAFE"] = "1"


class RecordingRun:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        self.calls.append(list(cmd))
        return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="")


def main() -> int:
    from runtime import runtime

    runtime.dry_run = True

    from categories import CATEGORIES

    print("Categories:", [c.title for c in CATEGORIES])
    for c in CATEGORIES:
        print(f"  {c.title}: {[m.title for m in c.modules]}")
    print()

    failures: list[str] = []

    for category in CATEGORIES:
        for module in category.modules:
            recorder = RecordingRun()
            with patch("subprocess.run", recorder):
                print(f"--- {category.title} / {module.title} ---")
                try:
                    module.run()
                except SystemExit as exc:
                    failures.append(
                        f"{module.key}: raised SystemExit({exc.code}) — "
                        f"mutation attempted under SAFE mode"
                    )
                except Exception as exc:
                    failures.append(f"{module.key}: raised {type(exc).__name__}: {exc}")
                print(f"  recorded {len(recorder.calls)} subprocess call(s)")
                for call in recorder.calls:
                    print(f"    {' '.join(str(p) for p in call)}")
                print()

    if failures:
        print("FAILURES:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("Smoke test OK — no module mutated the host.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

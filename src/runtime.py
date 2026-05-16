from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Runtime:
    dry_run: bool = False


runtime: Runtime = Runtime()

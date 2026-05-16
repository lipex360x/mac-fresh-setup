from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

ALL_PLATFORMS: frozenset[str] = frozenset({"darwin", "linux", "win32"})


@dataclass(frozen=True)
class Module:
    key: str
    title: str
    description: str
    run: Callable[[], None]
    platforms: frozenset[str] = field(default_factory=lambda: ALL_PLATFORMS)


@dataclass(frozen=True)
class Category:
    key: str
    title: str
    modules: tuple[Module, ...]

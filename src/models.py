from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Module:
    key: str
    title: str
    description: str
    run: Callable[[], None]


@dataclass(frozen=True)
class Category:
    key: str
    title: str
    modules: tuple[Module, ...]

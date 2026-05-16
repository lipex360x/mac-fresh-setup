from __future__ import annotations

from models import Category
from modules import ssh_key, sudoers

CATEGORIES: list[Category] = [
    Category(
        key="system",
        title="System",
        modules=(sudoers.module, ssh_key.module),
    ),
]

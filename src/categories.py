from __future__ import annotations

from models import Category
from modules import homebrew_install, ssh_key, sudoers, xcode_cli

CATEGORIES: list[Category] = [
    Category(
        key="system",
        title="System",
        modules=(sudoers.module, xcode_cli.module, ssh_key.module),
    ),
    Category(
        key="package_manager",
        title="Package manager",
        modules=(homebrew_install.module,),
    ),
]

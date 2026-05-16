from __future__ import annotations

from models import Category
from modules import (
    homebrew_casks,
    homebrew_formulae,
    homebrew_install,
    iterm2_prefs,
    ssh_key,
    sudoers,
    xcode_cli,
)

CATEGORIES: list[Category] = [
    Category(
        key="system",
        title="System",
        modules=(sudoers.module, xcode_cli.module, ssh_key.module),
    ),
    Category(
        key="package_manager",
        title="Package manager",
        modules=(
            homebrew_install.module,
            homebrew_formulae.module,
            homebrew_casks.module,
        ),
    ),
    Category(
        key="styling",
        title="Styling",
        modules=(iterm2_prefs.module,),
    ),
]

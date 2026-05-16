from __future__ import annotations

from models import Category
from modules.editor import vscode_extensions, vscode_settings
from modules.package_manager import homebrew_casks, homebrew_formulae, homebrew_install
from modules.styling import iterm2_prefs, oh_my_zsh, spaceship, zshrc
from modules.system import ssh_key, sudoers, xcode_cli

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
        modules=(
            iterm2_prefs.module,
            oh_my_zsh.module,
            spaceship.module,
            zshrc.module,
        ),
    ),
    Category(
        key="editor",
        title="Editor",
        modules=(vscode_extensions.module, vscode_settings.module),
    ),
]

from __future__ import annotations

from models import Category
from modules.editor import vscode_extensions, vscode_settings
from modules.package_manager import claude_code, homebrew_install, homebrew_packages, mise_runtimes
from modules.styling import iterm2_prefs, oh_my_zsh, spaceship, zsh_stack, zshrc
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
            claude_code.module,
            homebrew_install.module,
            homebrew_packages.module,
            mise_runtimes.module,
        ),
    ),
    Category(
        key="styling",
        title="Styling",
        modules=(
            iterm2_prefs.module,
            zsh_stack.module,
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

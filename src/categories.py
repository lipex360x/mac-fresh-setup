from __future__ import annotations

from models import Category
from modules.databases import mysql, postgres
from modules.package_manager import (
    chocolatey_install,
    chocolatey_packages,
    claude_code,
    homebrew_install,
    homebrew_packages,
    mise_runtimes,
)
from modules.styling import iterm2_prefs, vscode_stack, zsh_stack
from modules.system import git_for_windows, ssh_key, sudoers, xcode_cli

CATEGORIES: list[Category] = [
    Category(
        key="system",
        title="System",
        modules=(
            git_for_windows.module,
            sudoers.module,
            xcode_cli.module,
            ssh_key.module,
        ),
    ),
    Category(
        key="package_manager",
        title="Package manager",
        modules=(
            claude_code.module,
            homebrew_install.module,
            chocolatey_install.module,
            homebrew_packages.module,
            chocolatey_packages.module,
            mise_runtimes.module,
        ),
    ),
    Category(
        key="styling",
        title="Styling",
        modules=(
            iterm2_prefs.module,
            zsh_stack.module,
            vscode_stack.module,
        ),
    ),
    Category(
        key="databases",
        title="Databases",
        modules=(mysql.module, postgres.module),
    ),
]

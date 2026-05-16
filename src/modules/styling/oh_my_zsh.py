from __future__ import annotations

import os
import subprocess
from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_INSTALL_SCRIPT_URL = (
    "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
)
_OMZ_DIR = Path.home() / ".oh-my-zsh"


def _omz_installed() -> bool:
    return _OMZ_DIR.is_dir() and (_OMZ_DIR / "oh-my-zsh.sh").is_file()


def _fetch_install_script() -> str:
    result = subprocess.run(
        ["curl", "-fsSL", _INSTALL_SCRIPT_URL],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def install_oh_my_zsh() -> None:
    if _omz_installed():
        console.print(
            f"[yellow]Oh-my-zsh already installed at {_OMZ_DIR} — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch [dim]{_INSTALL_SCRIPT_URL}[/dim] "
            "and pipe it into [dim]sh[/dim] with [dim]RUNZSH=no CHSH=no "
            "KEEP_ZSHRC=yes[/dim]."
        )
        return

    script = _fetch_install_script()
    env = os.environ.copy()
    env.update({"RUNZSH": "no", "CHSH": "no", "KEEP_ZSHRC": "yes"})

    result = mutating_run(
        ["sh"],
        input=script,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        console.print(
            f"[red]Oh-my-zsh install exited with code {result.returncode}.[/red]"
        )
        return

    if not _omz_installed():
        console.print(
            f"[red]Install finished but {_OMZ_DIR} was not created.[/red]"
        )
        return

    console.print(f"[green]Oh-my-zsh installed at {_OMZ_DIR}.[/green]")


module = Module(
    key="oh_my_zsh",
    title="Oh-my-zsh",
    description="Installs oh-my-zsh via the official install.sh (no auto-shell-change, keeps existing .zshrc).",
    run=install_oh_my_zsh,
)

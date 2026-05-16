from __future__ import annotations

import shutil
import subprocess

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_INSTALL_URL = "https://claude.ai/install.sh"


def _claude_installed() -> bool:
    return shutil.which("claude") is not None


def _fetch_install_script() -> str:
    result = subprocess.run(
        ["curl", "-fsSL", _INSTALL_URL],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def install_claude_code() -> None:
    if _claude_installed():
        path = shutil.which("claude")
        console.print(
            f"[yellow]Claude Code already installed at {path} — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch [dim]{_INSTALL_URL}[/dim] and "
            "pipe it into [dim]bash[/dim] to install Claude Code into "
            "[dim]~/.local/bin[/dim]."
        )
        return

    console.print(
        "[bold]Installing Claude Code[/bold] — live output from Anthropic's "
        "installer below."
    )
    script = _fetch_install_script()
    result = mutating_run(["bash"], input=script, text=True)
    if result.returncode != 0:
        console.print(f"[red]Claude Code install failed (rc={result.returncode}).[/red]")
        return

    if not _claude_installed():
        console.print(
            "[yellow]Install finished but `claude` is not on PATH in this "
            "shell yet.[/yellow] Open a new terminal (or run "
            "[dim]source ~/.local/bin/env[/dim] / restart your shell) so the "
            "installer's PATH change takes effect."
        )
        return

    console.print(
        f"[green]Claude Code installed at {shutil.which('claude')}.[/green]"
    )


module = Module(
    key="claude_code",
    title="Claude Code",
    description="Anthropic's CLI — installed via the official native installer (curl | bash). No Node or brew required.",
    run=install_claude_code,
)

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_INSTALL_URL = "https://claude.ai/install.sh"
_ALIAS_LINE = "alias cc='claude --dangerously-skip-permissions'"
_ALIAS_BLOCK = f"\n### CLAUDE CODE\n{_ALIAS_LINE}\n"


def _claude_installed() -> bool:
    return shutil.which("claude") is not None


def _zshrc_path() -> Path:
    return Path.home() / ".zshrc"


def _alias_present(zshrc: Path) -> bool:
    if not zshrc.exists():
        return False
    return _ALIAS_LINE in zshrc.read_text()


def _inject_alias() -> None:
    zshrc = _zshrc_path()
    if _alias_present(zshrc):
        console.print(
            f"[yellow]`cc` alias already in {zshrc} — skipping injection.[/yellow]"
        )
        return
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would append [dim]{_ALIAS_LINE}[/dim] to "
            f"[dim]{zshrc}[/dim]."
        )
        return
    mutating_check(f"append `cc` alias to {zshrc}")
    existing = zshrc.read_text() if zshrc.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    zshrc.write_text(existing + _ALIAS_BLOCK)
    console.print(
        f"[green]Added `cc` alias to {zshrc}.[/green] Reopen your shell (or "
        f"run [dim]source {zshrc}[/dim]) to use it."
    )


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
            f"[yellow]Claude Code already installed at {path} — skipping binary install.[/yellow]"
        )
        _inject_alias()
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch [dim]{_INSTALL_URL}[/dim] and "
            "pipe it into [dim]bash[/dim] to install Claude Code into "
            "[dim]~/.local/bin[/dim]."
        )
        _inject_alias()
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

    else:
        console.print(
            f"[green]Claude Code installed at {shutil.which('claude')}.[/green]"
        )

    _inject_alias()


module = Module(
    key="claude_code",
    title="Claude Code",
    description="Anthropic's CLI — installed via the official native installer (curl | bash). No Node or brew required.",
    run=install_claude_code,
)

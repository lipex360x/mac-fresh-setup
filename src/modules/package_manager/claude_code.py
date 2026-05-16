from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_INSTALL_URL_POSIX = "https://claude.ai/install.sh"
_INSTALL_URL_WINDOWS = "https://claude.ai/install.ps1"
_ALIAS_LINE = "alias cc='claude --dangerously-skip-permissions'"
_ALIAS_BLOCK = f"\n### CLAUDE CODE\n{_ALIAS_LINE}\n"


def _claude_installed() -> bool:
    return shutil.which("claude") is not None


def _rc_path() -> Path:
    if sys.platform == "win32":
        return Path.home() / ".bashrc"
    return Path.home() / ".zshrc"


def _alias_present(rc: Path) -> bool:
    if not rc.exists():
        return False
    return _ALIAS_LINE in rc.read_text()


def _inject_alias() -> None:
    rc = _rc_path()
    if _alias_present(rc):
        console.print(
            f"[yellow]`cc` alias already in {rc} — skipping injection.[/yellow]"
        )
        return
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would append [dim]{_ALIAS_LINE}[/dim] to "
            f"[dim]{rc}[/dim]."
        )
        return
    mutating_check(f"append `cc` alias to {rc}")
    existing = rc.read_text() if rc.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    rc.write_text(existing + _ALIAS_BLOCK)
    console.print(
        f"[green]Added `cc` alias to {rc}.[/green] Reopen your shell (or "
        f"run [dim]source {rc}[/dim]) to use it."
    )


def _fetch_install_script_posix() -> str:
    result = subprocess.run(
        ["curl", "-fsSL", _INSTALL_URL_POSIX],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _install_posix() -> int:
    script = _fetch_install_script_posix()
    result = mutating_run(["bash"], input=script, text=True)
    return result.returncode


def _install_windows() -> int:
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f"irm {_INSTALL_URL_WINDOWS} | iex",
    ]
    result = mutating_run(cmd)
    return result.returncode


def _install_url() -> str:
    return _INSTALL_URL_WINDOWS if sys.platform == "win32" else _INSTALL_URL_POSIX


def _install_summary() -> str:
    if sys.platform == "win32":
        return (
            f"fetch [dim]{_INSTALL_URL_WINDOWS}[/dim] and pipe it into "
            "[dim]powershell -Command 'iex'[/dim] to install Claude Code into "
            r"[dim]%USERPROFILE%\.local\bin[/dim]"
        )
    return (
        f"fetch [dim]{_INSTALL_URL_POSIX}[/dim] and pipe it into [dim]bash[/dim] "
        "to install Claude Code into [dim]~/.local/bin[/dim]"
    )


def install_claude_code() -> None:
    if _claude_installed():
        path = shutil.which("claude")
        console.print(
            f"[yellow]Claude Code already installed at {path} — skipping binary install.[/yellow]"
        )
        _inject_alias()
        return

    if runtime.dry_run:
        console.print(f"[cyan]DRY RUN[/cyan] would {_install_summary()}.")
        _inject_alias()
        return

    console.print(
        "[bold]Installing Claude Code[/bold] — live output from Anthropic's "
        "installer below."
    )
    rc = _install_windows() if sys.platform == "win32" else _install_posix()
    if rc != 0:
        console.print(f"[red]Claude Code install failed (rc={rc}).[/red]")
        return

    if not _claude_installed():
        hint = (
            "source ~/.bashrc (Git Bash) or open a new terminal"
            if sys.platform == "win32"
            else "source ~/.local/bin/env / restart your shell"
        )
        console.print(
            "[yellow]Install finished but `claude` is not on PATH in this "
            f"shell yet.[/yellow] Open a new terminal (or run [dim]{hint}[/dim]) "
            "so the installer's PATH change takes effect."
        )
    else:
        console.print(
            f"[green]Claude Code installed at {shutil.which('claude')}.[/green]"
        )

    _inject_alias()


module = Module(
    key="claude_code",
    title="Claude Code",
    description=(
        "Anthropic's CLI — installed via the official native installer "
        "(curl | bash on macOS/Linux, PowerShell `irm | iex` on Windows). "
        "No Node or brew required."
    ),
    run=install_claude_code,
)

from __future__ import annotations

import shutil
from pathlib import Path

from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_INSTALL_URL = "https://get.scoop.sh"
_DEFAULT_SCOOP_DIR = Path.home() / "scoop"
_DEFAULT_SHIMS = _DEFAULT_SCOOP_DIR / "shims"
_PS_INSTALL_SNIPPET = (
    "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force; "
    f"irm {_INSTALL_URL} | iex"
)


def _scoop_path() -> Path | None:
    found = shutil.which("scoop")
    if found:
        return Path(found)
    for candidate in (_DEFAULT_SHIMS / "scoop.cmd", _DEFAULT_SHIMS / "scoop.ps1"):
        if candidate.exists():
            return candidate
    return None


def install_scoop() -> None:
    scoop = _scoop_path()
    if scoop is not None:
        console.print(
            f"[yellow]Scoop already installed at {scoop} — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would run [dim]powershell -Command "
            f"\"{_PS_INSTALL_SNIPPET}\"[/dim]. Scoop installs under "
            f"[dim]{_DEFAULT_SCOOP_DIR}[/dim] (no admin / no UAC required)."
        )
        return

    console.print(
        Panel.fit(
            "[bold]Installing Scoop[/bold]\n\n"
            "User-level Windows package manager — installs under "
            f"[dim]{_DEFAULT_SCOOP_DIR}[/dim]. [bold green]No admin / no UAC "
            "required.[/bold green]",
            border_style="cyan",
            title="Scoop",
        )
    )

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        _PS_INSTALL_SNIPPET,
    ]
    result = mutating_run(cmd)
    if result.returncode != 0:
        console.print(
            f"[red]Scoop installer exited with code {result.returncode}.[/red]"
        )
        return

    scoop = _scoop_path()
    if scoop is None:
        console.print(
            f"[red]Installer ran but `scoop` is not on PATH or under "
            f"{_DEFAULT_SHIMS}.[/red] Open a new terminal (PATH refresh) and "
            "re-run to verify."
        )
        return

    console.print(
        Panel.fit(
            f"[green]Scoop installed at {scoop}.[/green]\n\n"
            "[bold]Next:[/bold] open a new Git Bash window so "
            "[dim]scoop[/dim] lands on PATH for [dim]Scoop packages[/dim].",
            border_style="green",
            title="Installed",
        )
    )


module = Module(
    key="scoop_install",
    title="Scoop",
    description=(
        "Installs Scoop via the official PowerShell script — user-level, no admin / no UAC. "
        "Windows analogue to Homebrew for non-administrator setups."
    ),
    run=install_scoop,
    platforms=frozenset({"win32"}),
)

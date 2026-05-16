from __future__ import annotations

import shutil
from pathlib import Path

from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_INSTALL_URL = "https://community.chocolatey.org/install.ps1"
_DEFAULT_CHOCO_BIN = Path(r"C:\ProgramData\chocolatey\bin\choco.exe")
_PS_INSTALL_SNIPPET = (
    "Set-ExecutionPolicy Bypass -Scope Process -Force; "
    "[System.Net.ServicePointManager]::SecurityProtocol = "
    "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
    f"iex ((New-Object System.Net.WebClient).DownloadString('{_INSTALL_URL}'))"
)


def _choco_path() -> Path | None:
    found = shutil.which("choco")
    if found:
        return Path(found)
    if _DEFAULT_CHOCO_BIN.exists():
        return _DEFAULT_CHOCO_BIN
    return None


def _elevated_install_cmd() -> list[str]:
    inner = (
        "Start-Process powershell -Verb RunAs -Wait -ArgumentList "
        f"'-NoProfile','-ExecutionPolicy','Bypass','-Command',\"{_PS_INSTALL_SNIPPET}\""
    )
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", inner]


def install_chocolatey() -> None:
    choco = _choco_path()
    if choco is not None:
        console.print(
            f"[yellow]Chocolatey already installed at {choco} — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would launch an elevated PowerShell (UAC prompt) "
            f"and run the official installer from [dim]{_INSTALL_URL}[/dim]. "
            f"Choco lands at [dim]{_DEFAULT_CHOCO_BIN}[/dim]."
        )
        return

    console.print(
        Panel.fit(
            "[bold]Installing Chocolatey[/bold]\n\n"
            "A [bold yellow]UAC prompt[/bold yellow] will appear — accept it. "
            "The elevated PowerShell window runs the official installer and closes "
            "when done.",
            border_style="cyan",
            title="Chocolatey",
        )
    )

    result = mutating_run(_elevated_install_cmd())
    if result.returncode != 0:
        console.print(
            f"[red]Elevated PowerShell exited with code {result.returncode}.[/red] "
            "If you cancelled UAC, re-run this module."
        )
        return

    choco = _choco_path()
    if choco is None:
        console.print(
            "[red]Installer ran but `choco` is not on PATH or at the default location.[/red] "
            "Open a new terminal (PATH refresh) and re-run to verify, or run the installer manually."
        )
        return

    console.print(
        Panel.fit(
            f"[green]Chocolatey installed at {choco}.[/green]\n\n"
            "[bold]Next:[/bold] close this terminal and open a new Git Bash window "
            "so [dim]choco[/dim] lands on PATH for subsequent modules.",
            border_style="green",
            title="Installed",
        )
    )


module = Module(
    key="chocolatey_install",
    title="Chocolatey",
    description=(
        "Installs Chocolatey via the official PowerShell script (elevated UAC prompt). "
        "Windows analogue to Homebrew."
    ),
    run=install_chocolatey,
    platforms=frozenset({"win32"}),
)

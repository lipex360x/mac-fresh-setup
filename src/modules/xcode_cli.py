from __future__ import annotations

import subprocess

import questionary
from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime


def _developer_dir() -> str | None:
    result = subprocess.run(
        ["xcode-select", "-p"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    path = result.stdout.strip()
    return path or None


def _clt_installed() -> bool:
    result = subprocess.run(
        ["pkgutil", "--pkg-info=com.apple.pkg.CLTools_Executables"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def install_xcode_cli() -> None:
    if _clt_installed():
        path = _developer_dir() or "unknown"
        console.print(
            f"[yellow]XCode Command Line Tools already installed (developer dir: {path}) — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            "[cyan]DRY RUN[/cyan] would run [dim]xcode-select --install[/dim], "
            "wait for the GUI dialog to finish, then verify via "
            "[dim]pkgutil --pkg-info=com.apple.pkg.CLTools_Executables[/dim]."
        )
        return

    console.print(
        Panel.fit(
            "[bold]xcode-select --install will open a system dialog.[/bold]\n"
            "Click [bold cyan]Install[/bold cyan] in the dialog, accept the licence,\n"
            "and wait for it to finish (this can take several minutes).\n"
            "Then return here and press any key.",
            border_style="cyan",
        )
    )

    trigger = subprocess.run(
        ["xcode-select", "--install"],
        capture_output=True,
        text=True,
    )
    if trigger.returncode != 0 and "already installed" not in (trigger.stderr or ""):
        console.print(f"[red]xcode-select --install failed:[/red] {trigger.stderr.strip()}")

    questionary.press_any_key_to_continue(
        "Press any key once the install finishes..."
    ).ask()

    if not _clt_installed():
        console.print(
            "[red]Command Line Tools not detected after install. "
            "Re-run this module after the dialog completes.[/red]"
        )
        return

    path = _developer_dir() or "unknown"
    console.print(
        f"[green]XCode Command Line Tools installed (developer dir: {path}).[/green]"
    )


module = Module(
    key="xcode_cli",
    title="XCode Command Line Tools",
    description="Triggers xcode-select --install and waits for the system dialog to finish.",
    run=install_xcode_cli,
)

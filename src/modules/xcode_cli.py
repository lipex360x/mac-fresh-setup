from __future__ import annotations

import subprocess
from pathlib import Path

import questionary
from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run


def _developer_dir() -> Path | None:
    result = subprocess.run(
        ["xcode-select", "-p"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    return Path(raw) if raw else None


def _clt_installed() -> bool:
    dev_dir = _developer_dir()
    if dev_dir is None or not dev_dir.exists():
        return False
    return (dev_dir / "usr" / "bin" / "clang").exists()


def _diagnose() -> None:
    sel = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True)
    console.print(
        f"[dim]xcode-select -p → rc={sel.returncode}, "
        f"stdout={sel.stdout.strip()!r}, stderr={sel.stderr.strip()!r}[/dim]"
    )
    dev = _developer_dir()
    if dev is not None:
        clang = dev / "usr" / "bin" / "clang"
        console.print(
            f"[dim]developer dir exists? {dev.exists()} — "
            f"clang at {clang} exists? {clang.exists()}[/dim]"
        )


def install_xcode_cli() -> None:
    if _clt_installed():
        dev = _developer_dir()
        console.print(
            f"[yellow]XCode Command Line Tools already installed "
            f"(developer dir: {dev}) — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            "[cyan]DRY RUN[/cyan] would run [dim]xcode-select --install[/dim], "
            "wait for the GUI dialog to finish, then verify via "
            "[dim]xcode-select -p[/dim] + clang existence."
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

    trigger = mutating_run(
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
            "[red]Command Line Tools not detected after install.[/red] Diagnostic:"
        )
        _diagnose()
        console.print(
            "[yellow]If the dialog is still running, wait for it to finish and "
            "re-run this module.[/yellow]"
        )
        return

    dev = _developer_dir()
    console.print(
        f"[green]XCode Command Line Tools installed (developer dir: {dev}).[/green]"
    )


module = Module(
    key="xcode_cli",
    title="XCode Command Line Tools",
    description="Triggers xcode-select --install and waits for the system dialog to finish.",
    run=install_xcode_cli,
)

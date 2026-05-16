from __future__ import annotations

import subprocess
import time
from pathlib import Path

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_POLL_INTERVAL_SECONDS = 5
_DEFAULT_TIMEOUT_SECONDS = 900


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


def _wait_for_install(timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout_seconds
    with Progress(
        SpinnerColumn(),
        TextColumn(
            "[cyan]Waiting for Command Line Tools to finish installing"
            " (Ctrl+C to abort)..."
        ),
        transient=False,
    ) as progress:
        progress.add_task("clt", total=None)
        while time.monotonic() < deadline:
            if _clt_installed():
                return True
            time.sleep(_POLL_INTERVAL_SECONDS)
    return False


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
            "poll [dim]xcode-select -p[/dim] every "
            f"{_POLL_INTERVAL_SECONDS}s until clang exists "
            f"(timeout {_DEFAULT_TIMEOUT_SECONDS // 60} min)."
        )
        return

    console.print(
        Panel.fit(
            "[bold]A system dialog will open in a moment.[/bold]\n"
            "Click [bold cyan]Install[/bold cyan], accept the licence, "
            "and let it finish.\n"
            "This script will detect completion automatically — no key press needed.",
            border_style="cyan",
        )
    )

    trigger = mutating_run(
        ["xcode-select", "--install"],
        capture_output=True,
        text=True,
    )
    stderr = (trigger.stderr or "").strip()
    if trigger.returncode != 0 and "already installed" not in stderr:
        console.print(f"[red]xcode-select --install failed:[/red] {stderr}")

    try:
        installed = _wait_for_install()
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user.[/yellow]")
        _diagnose()
        return

    if not installed:
        console.print(
            f"[red]Timed out after {_DEFAULT_TIMEOUT_SECONDS // 60} minutes. "
            "Diagnostic:[/red]"
        )
        _diagnose()
        console.print(
            "[yellow]If the dialog never appeared, try running "
            "[dim]sudo xcode-select --install[/dim] manually in another terminal, "
            "then re-run this module.[/yellow]"
        )
        return

    dev = _developer_dir()
    console.print(
        f"[green]XCode Command Line Tools installed (developer dir: {dev}).[/green]"
    )


module = Module(
    key="xcode_cli",
    title="XCode Command Line Tools",
    description="Triggers xcode-select --install and polls until CLT is detected.",
    run=install_xcode_cli,
)

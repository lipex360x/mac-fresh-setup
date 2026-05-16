from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_TRIGGER_FILE = Path("/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress")
_POLL_INTERVAL_SECONDS = 5
_DEFAULT_TIMEOUT_SECONDS = 900
_LIST_TIMEOUT_SECONDS = 180
_INSTALLER_GRACE_SECONDS = 15
_INSTALLER_PROCESS_NAME = "Install Command Line Developer Tools"


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


def _find_clt_label() -> str | None:
    console.print(
        "[dim]Querying softwareupdate for the Command Line Tools package "
        "(can take ~30s)...[/dim]"
    )
    try:
        result = subprocess.run(
            ["softwareupdate", "--list"],
            capture_output=True,
            text=True,
            timeout=_LIST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        console.print("[yellow]softwareupdate --list timed out.[/yellow]")
        return None
    if result.returncode != 0:
        return None
    labels: list[str] = []
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*\*\s*Label:\s*(.+)$", line)
        if match and "Command Line Tools" in match.group(1):
            labels.append(match.group(1).strip())
    if not labels:
        return None
    return sorted(labels)[-1]


def _install_via_softwareupdate(label: str) -> bool:
    console.print(
        Panel.fit(
            f"Installing [bold cyan]{label}[/bold cyan] via "
            "[dim]softwareupdate[/dim].\n"
            "Live progress from macOS below — this can take several minutes.",
            border_style="cyan",
        )
    )
    result = mutating_run(
        [
            "sudo",
            "softwareupdate",
            "--install",
            "--no-scan",
            "--agree-to-license",
            label,
        ],
    )
    return result.returncode == 0


def _installer_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-x", _INSTALLER_PROCESS_NAME],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _install_via_dialog() -> bool:
    console.print(
        Panel.fit(
            "[bold]Falling back to the GUI install dialog.[/bold]\n"
            "A system dialog will open in a moment — click "
            "[bold cyan]Install[/bold cyan] and let it finish.\n"
            "This script will detect completion automatically; if the dialog "
            "is closed without installing, it bails out promptly.",
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
        return False

    deadline = time.monotonic() + _DEFAULT_TIMEOUT_SECONDS
    grace_deadline = time.monotonic() + _INSTALLER_GRACE_SECONDS
    installer_seen = False

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Waiting for CLT install (Ctrl+C to abort)"),
        TimeElapsedColumn(),
        transient=False,
    ) as progress:
        progress.add_task("clt", total=None)
        while time.monotonic() < deadline:
            if _clt_installed():
                return True

            running = _installer_running()
            if running:
                installer_seen = True
            elif installer_seen:
                console.print(
                    "[yellow]Installer process closed without installing CLT "
                    "(dialog cancelled or failed).[/yellow]"
                )
                return False
            elif time.monotonic() > grace_deadline:
                console.print(
                    f"[yellow]Installer process [dim]{_INSTALLER_PROCESS_NAME}[/dim] "
                    f"never started within {_INSTALLER_GRACE_SECONDS}s — "
                    "the dialog likely could not open.[/yellow]"
                )
                return False

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
            "[cyan]DRY RUN[/cyan] would touch "
            f"[dim]{_TRIGGER_FILE}[/dim], find the CLT label via "
            "[dim]softwareupdate --list[/dim], then run "
            "[dim]sudo softwareupdate --install --agree-to-license <label>[/dim] "
            "with live output (fallback: [dim]xcode-select --install[/dim] "
            "with polling)."
        )
        return

    mutating_check(f"touch {_TRIGGER_FILE}")
    _TRIGGER_FILE.touch()

    try:
        label = _find_clt_label()
        if label is not None:
            ok = _install_via_softwareupdate(label)
        else:
            console.print(
                "[yellow]No Command Line Tools package found via "
                "softwareupdate — falling back to GUI dialog.[/yellow]"
            )
            ok = _install_via_dialog()
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user.[/yellow]")
        ok = False
    finally:
        _TRIGGER_FILE.unlink(missing_ok=True)

    if not ok or not _clt_installed():
        console.print("[red]Install failed or CLT not detected. Diagnostic:[/red]")
        _diagnose()
        return

    dev = _developer_dir()
    console.print(
        f"[green]XCode Command Line Tools installed (developer dir: {dev}).[/green]"
    )


module = Module(
    key="xcode_cli",
    title="XCode Command Line Tools",
    description="Installs Command Line Tools via softwareupdate (live progress) with GUI dialog fallback.",
    run=install_xcode_cli,
    platforms=frozenset({"darwin"}),
)

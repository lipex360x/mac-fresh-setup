from __future__ import annotations

import os
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_ITERM2_PLIST = Path.home() / "Library" / "Preferences" / "com.googlecode.iterm2.plist"
_DOWNLOADS_FALLBACK = Path.home() / "Downloads" / "com.googlecode.iterm2.plist"
_ENV_VAR = "ITERM2_PREFS_URL"
_DEFAULT_URL = (
    "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/"
    "config/iterm2/com.googlecode.iterm2.plist"
)


def _resolve_source() -> str:
    override = os.environ.get(_ENV_VAR, "").strip()
    if override:
        console.print(f"[dim]Using ${_ENV_VAR} override: {override}[/dim]")
        return override
    console.print(f"[dim]Using bundled prefs: {_DEFAULT_URL}[/dim]")
    return _DEFAULT_URL


def _fetch_bytes(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            return response.read()
    src_path = Path(source).expanduser()
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    return src_path.read_bytes()


def _try_direct_injection(data: bytes) -> bool:
    try:
        _ITERM2_PLIST.parent.mkdir(parents=True, exist_ok=True)
        if _ITERM2_PLIST.exists():
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = _ITERM2_PLIST.with_suffix(f".plist.bak-{stamp}")
            shutil.copyfile(_ITERM2_PLIST, backup)
            console.print(f"[dim]Existing plist backed up to {backup}.[/dim]")
        _ITERM2_PLIST.write_bytes(data)
    except OSError as exc:
        console.print(f"[yellow]Direct write failed: {exc}[/yellow]")
        return False
    mutating_run(
        ["killall", "cfprefsd"],
        capture_output=True,
        text=True,
    )
    return True


def _save_to_downloads(data: bytes) -> Path:
    _DOWNLOADS_FALLBACK.parent.mkdir(parents=True, exist_ok=True)
    _DOWNLOADS_FALLBACK.write_bytes(data)
    return _DOWNLOADS_FALLBACK


def sync_iterm2_prefs() -> None:
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch the plist from "
            f"[dim]{_DEFAULT_URL}[/dim] (or [dim]${_ENV_VAR}[/dim] override), "
            f"write it to [dim]{_ITERM2_PLIST}[/dim] (backing up existing), run "
            "[dim]killall cfprefsd[/dim], and on failure fall back to "
            f"[dim]{_DOWNLOADS_FALLBACK}[/dim] with manual import instructions."
        )
        return

    source = _resolve_source()

    mutating_check(f"write iTerm2 prefs (target: {_ITERM2_PLIST})")

    try:
        data = _fetch_bytes(source)
    except (FileNotFoundError, urllib.error.URLError, OSError) as exc:
        console.print(f"[red]Failed to read source:[/red] {exc}")
        return

    if _try_direct_injection(data):
        console.print(
            Panel.fit(
                f"[green]iTerm2 preferences injected at[/green] "
                f"[bold]{_ITERM2_PLIST}[/bold].\n"
                "[bold]cfprefsd[/bold] cache was invalidated. "
                "Quit iTerm2 (⌘Q) and reopen — settings will be active.",
                border_style="green",
            )
        )
        return

    fallback = _save_to_downloads(data)
    console.print(
        Panel(
            f"[yellow]Direct injection failed.[/yellow]\n"
            f"Plist saved to [bold]{fallback}[/bold].\n\n"
            "[bold]To import manually:[/bold]\n"
            "1. Quit iTerm2 entirely (⌘Q).\n"
            f"2. Copy the file: [dim]cp {fallback} {_ITERM2_PLIST}[/dim]\n"
            "3. Invalidate cache: [dim]killall cfprefsd[/dim]\n"
            "4. Reopen iTerm2.\n\n"
            "Alternative — use iTerm2's [dim]Settings → General → Preferences → "
            "Load settings from a custom folder or URL[/dim] and point at the "
            "source URL.",
            border_style="yellow",
            title="Fallback",
        )
    )


module = Module(
    key="iterm2_prefs",
    title="iTerm2 preferences",
    description="Inject iTerm2 plist (with cfprefsd cache invalidation); falls back to ~/Downloads if blocked.",
    run=sync_iterm2_prefs,
)

from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import questionary
from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check

_SETTINGS_PATH = (
    Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
)
_ENV_VAR = "VSCODE_SETTINGS_URL"


def _read_source() -> str | None:
    default = os.environ.get(_ENV_VAR, "")
    if default:
        console.print(f"[dim]Using ${_ENV_VAR} = {default}[/dim]")
        return default
    source = questionary.text(
        "VSCode settings source (URL or local path to settings.json) — "
        "leave empty to cancel:",
        default="",
    ).ask()
    if source is None:
        return None
    source = source.strip()
    return source or None


def _fetch_bytes(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            return response.read()
    src_path = Path(source).expanduser()
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    return src_path.read_bytes()


def sync_vscode_settings() -> None:
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would read source from [dim]${_ENV_VAR}[/dim] "
            "(or prompt), fetch the bytes, back up any existing file, and write "
            f"to [dim]{_SETTINGS_PATH}[/dim]."
        )
        return

    source = _read_source()
    if source is None:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    mutating_check(f"write VSCode settings at {_SETTINGS_PATH}")

    try:
        data = _fetch_bytes(source)
    except (FileNotFoundError, urllib.error.URLError, OSError) as exc:
        console.print(f"[red]Failed to read source:[/red] {exc}")
        return

    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _SETTINGS_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = _SETTINGS_PATH.with_suffix(f".json.bak-{stamp}")
        shutil.copyfile(_SETTINGS_PATH, backup)
        console.print(f"[dim]Existing settings backed up to {backup}.[/dim]")

    _SETTINGS_PATH.write_bytes(data)
    console.print(
        Panel.fit(
            f"[green]VSCode settings written to[/green] [bold]{_SETTINGS_PATH}[/bold].\n"
            "Reload the window in VSCode (⌘⇧P → Developer: Reload Window) to apply.",
            border_style="green",
        )
    )


module = Module(
    key="vscode_settings",
    title="VSCode settings",
    description="Replace ~/Library/Application Support/Code/User/settings.json with a URL or local file.",
    run=sync_vscode_settings,
)

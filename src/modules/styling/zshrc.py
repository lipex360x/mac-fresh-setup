from __future__ import annotations

import os
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check

_ZSHRC_PATH = Path.home() / ".zshrc"
_ENV_VAR = "ZSHRC_URL"
_DEFAULT_URL = (
    "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/"
    "config/zsh/.zshrc"
)


def _resolve_source() -> str:
    override = os.environ.get(_ENV_VAR, "").strip()
    if override:
        console.print(f"[dim]Using ${_ENV_VAR} override: {override}[/dim]")
        return override
    console.print(f"[dim]Using bundled .zshrc: {_DEFAULT_URL}[/dim]")
    return _DEFAULT_URL


def _fetch_bytes(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            return response.read()
    src_path = Path(source).expanduser()
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    return src_path.read_bytes()


def sync_zshrc() -> None:
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch the .zshrc from "
            f"[dim]{_DEFAULT_URL}[/dim] (or [dim]${_ENV_VAR}[/dim] override), "
            f"back up any existing [dim]{_ZSHRC_PATH}[/dim], and write the new "
            "file."
        )
        return

    source = _resolve_source()
    mutating_check(f"write {_ZSHRC_PATH}")

    try:
        data = _fetch_bytes(source)
    except (FileNotFoundError, urllib.error.URLError, OSError) as exc:
        console.print(f"[red]Failed to read source:[/red] {exc}")
        return

    if _ZSHRC_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = _ZSHRC_PATH.with_name(f".zshrc.bak-{stamp}")
        shutil.copyfile(_ZSHRC_PATH, backup)
        console.print(f"[dim]Existing .zshrc backed up to {backup}.[/dim]")

    _ZSHRC_PATH.write_bytes(data)
    console.print(
        Panel.fit(
            f"[green]Wrote[/green] [bold]{_ZSHRC_PATH}[/bold].\n"
            "Open a new terminal (or run [bold]source ~/.zshrc[/bold]) "
            "to apply.",
            border_style="green",
        )
    )


module = Module(
    key="zshrc",
    title="Custom .zshrc",
    description="Replaces ~/.zshrc with the bundled config (OMZ + Spaceship + zinit plugins).",
    run=sync_zshrc,
)

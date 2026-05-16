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

_SETTINGS_PATH = (
    Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
)
_SETTINGS_URL = (
    "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/"
    "config/vscode/settings.json"
)
_EXTENSIONS_URL = (
    "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/"
    "config/vscode/extensions.txt"
)
_BUNDLED_CODE = Path(
    "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
)


def _code_binary() -> Path | None:
    found = shutil.which("code")
    if found:
        return Path(found)
    if _BUNDLED_CODE.exists():
        return _BUNDLED_CODE
    return None


def _installed_extensions(code_bin: Path) -> set[str]:
    result = subprocess.run(
        [str(code_bin), "--list-extensions"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}


def _fetch_bytes(url: str) -> bytes:
    if url.startswith(("http://", "https://")):
        with urllib.request.urlopen(url) as response:
            return response.read()
    src_path = Path(url).expanduser()
    if not src_path.is_file():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    return src_path.read_bytes()


def _fetch_extensions() -> list[str]:
    url = os.environ.get("VSCODE_EXTENSIONS_URL", "").strip() or _EXTENSIONS_URL
    data = _fetch_bytes(url)
    return [
        line.strip()
        for line in data.decode("utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _install_extensions(code_bin: Path) -> None:
    try:
        wanted = _fetch_extensions()
    except (FileNotFoundError, urllib.error.URLError, OSError) as exc:
        console.print(f"[red]Failed to read extensions list:[/red] {exc}")
        return

    installed = _installed_extensions(code_bin)
    pending = [ext for ext in wanted if ext.lower() not in installed]

    if not pending:
        console.print(
            f"[yellow]All {len(wanted)} bundled extensions already installed — "
            "skipping.[/yellow]"
        )
        return

    console.print(
        f"[bold]Installing {len(pending)} extension(s)[/bold] "
        f"({len(wanted) - len(pending)} already present)."
    )
    for ext_id in pending:
        console.rule(f"[bold]{code_bin.name} --install-extension {ext_id}[/bold]")
        result = mutating_run([str(code_bin), "--install-extension", ext_id])
        if result.returncode != 0:
            console.print(
                f"[red]Failed to install {ext_id} (rc={result.returncode}).[/red]"
            )


def _sync_settings() -> None:
    url = os.environ.get("VSCODE_SETTINGS_URL", "").strip() or _SETTINGS_URL
    try:
        data = _fetch_bytes(url)
    except (FileNotFoundError, urllib.error.URLError, OSError) as exc:
        console.print(f"[red]Failed to read settings.json source:[/red] {exc}")
        return

    mutating_check(f"write VSCode settings at {_SETTINGS_PATH}")
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _SETTINGS_PATH.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = _SETTINGS_PATH.with_name(f"settings.json.bak-{stamp}")
        shutil.copyfile(_SETTINGS_PATH, backup)
        console.print(f"[dim]Existing settings backed up to {backup}.[/dim]")
    _SETTINGS_PATH.write_bytes(data)
    console.print(
        Panel.fit(
            f"[green]VSCode settings written to[/green] [bold]{_SETTINGS_PATH}[/bold].\n"
            "Reload the window (⌘⇧P → Developer: Reload Window) to apply.",
            border_style="green",
        )
    )


def install_vscode_stack() -> None:
    code_bin = _code_binary()
    if code_bin is None:
        console.print(
            "[red]VSCode `code` CLI not found.[/red] Install "
            "[bold]visual-studio-code[/bold] via Package manager → Homebrew "
            "packages first, or run [dim]Cmd+Shift+P → Shell Command: "
            "Install 'code' command in PATH[/dim] inside VSCode."
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would fetch the extensions list from "
            f"[dim]{_EXTENSIONS_URL}[/dim] (or [dim]$VSCODE_EXTENSIONS_URL[/dim] "
            f"override), run [dim]{code_bin.name} --install-extension <id>[/dim] "
            "for each missing entry, then fetch the settings.json from "
            f"[dim]{_SETTINGS_URL}[/dim] (or [dim]$VSCODE_SETTINGS_URL[/dim] "
            f"override) and overwrite [dim]{_SETTINGS_PATH}[/dim] (backup kept)."
        )
        return

    console.rule("[bold cyan]1/2 — Extensions[/bold cyan]")
    _install_extensions(code_bin)
    console.rule("[bold cyan]2/2 — settings.json[/bold cyan]")
    _sync_settings()
    console.rule("[bold green]VSCode stack ready[/bold green]")


module = Module(
    key="vscode_stack",
    title="VSCode stack (extensions + settings)",
    description="Install the bundled VSCode extensions list and overwrite settings.json from the repo.",
    run=install_vscode_stack,
)

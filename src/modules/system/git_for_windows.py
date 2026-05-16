from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

_GIT_VERSION = "2.45.0"
_GIT_REV = "1"
_INSTALLER_URL = (
    f"https://github.com/git-for-windows/git/releases/download/"
    f"v{_GIT_VERSION}.windows.{_GIT_REV}/Git-{_GIT_VERSION}-64-bit.exe"
)
_DEFAULT_INSTALL_DIR = Path(r"C:\Program Files\Git")
_SILENT_FLAGS = ["/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES", "/SP-"]
_COMPONENTS = (
    "ext,ext\\reg\\shellhere,ext\\reg\\guihere,assoc,assoc_sh,gitlfs,scalar"
)


def git_present() -> bool:
    return shutil.which("git") is not None and shutil.which("bash") is not None


def _download_installer() -> Path:
    console.print(f"[dim]Downloading {_INSTALLER_URL}[/dim]")
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
        target = Path(tmp.name)
    with urllib.request.urlopen(_INSTALLER_URL) as response:
        target.write_bytes(response.read())
    return target


def install_git_for_windows() -> None:
    if git_present():
        console.print(
            f"[yellow]Git for Windows already installed "
            f"(git: {shutil.which('git')}, bash: {shutil.which('bash')}) — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would download [dim]{_INSTALLER_URL}[/dim] "
            "and run it with "
            f"[dim]{' '.join(_SILENT_FLAGS)} /COMPONENTS=\"{_COMPONENTS}\"[/dim]. "
            f"Default install dir: [dim]{_DEFAULT_INSTALL_DIR}[/dim]."
        )
        return

    installer = _download_installer()
    try:
        cmd = [str(installer), *_SILENT_FLAGS, f"/COMPONENTS={_COMPONENTS}"]
        console.print(f"[bold]Running Git for Windows installer[/bold]")
        rc = mutating_run(cmd).returncode
        if rc != 0:
            console.print(
                f"[red]Installer exited with code {rc}.[/red] "
                "Try running it manually from the downloaded path."
            )
            return
    finally:
        installer.unlink(missing_ok=True)

    if not git_present():
        console.print(
            "[red]Installer ran but `git` and/or `bash` are still not on PATH.[/red] "
            "Open a new shell first (PATH refresh) and re-run, or run the installer manually."
        )
        return

    console.print(
        Panel.fit(
            f"[green]Git for Windows {_GIT_VERSION} installed.[/green]\n"
            f"  git:  [dim]{shutil.which('git')}[/dim]\n"
            f"  bash: [dim]{shutil.which('bash')}[/dim]\n\n"
            "[bold]Next:[/bold] close this terminal and open "
            "[bold cyan]Git Bash[/bold cyan] (Start Menu) — every other module in "
            "this setup expects the Unix-style tools that Git Bash provides "
            "(`curl`, `tar`, `chmod`, `ssh-keygen`, …). Re-run:\n\n"
            "  [dim]uv run --refresh "
            "\"https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py\"[/dim]",
            border_style="green",
            title="Installed",
        )
    )


module = Module(
    key="git_for_windows",
    title="Git for Windows (bash + git + curl + tar + ssh-keygen)",
    description=(
        "Hard prerequisite on Windows. Installs Git for Windows silently "
        "so every other module's Unix-style commands work."
    ),
    run=install_git_for_windows,
    platforms=frozenset({"win32"}),
)

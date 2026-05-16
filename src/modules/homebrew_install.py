from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"


def _brew_path() -> Path | None:
    found = shutil.which("brew")
    if found:
        return Path(found)
    for candidate in (Path("/opt/homebrew/bin/brew"), Path("/usr/local/bin/brew")):
        if candidate.exists():
            return candidate
    return None


def _brew_prefix() -> Path:
    brew = _brew_path()
    if brew is not None:
        return brew.parent.parent
    return Path("/opt/homebrew") if platform.machine() == "arm64" else Path("/usr/local")


def _shellenv_line() -> str:
    return f'eval "$({_brew_prefix()}/bin/brew shellenv)"'


def _zprofile_path() -> Path:
    return Path.home() / ".zprofile"


def _shellenv_configured() -> bool:
    zp = _zprofile_path()
    if not zp.exists():
        return False
    return _shellenv_line() in zp.read_text()


def _fetch_install_script() -> str:
    result = subprocess.run(
        ["curl", "-fsSL", _INSTALL_SCRIPT_URL],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _install_brew() -> None:
    script = _fetch_install_script()
    env = os.environ.copy()
    env["NONINTERACTIVE"] = "1"
    result = mutating_run(
        ["/bin/bash"],
        input=script,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Homebrew install script exited with code {result.returncode}")


def _append_shellenv() -> None:
    zp = _zprofile_path()
    mutating_check(f"append brew shellenv to {zp}")
    existing = zp.read_text() if zp.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    header = "" if "brew shellenv" in existing else "# Homebrew\n"
    zp.write_text(existing + header + _shellenv_line() + "\n")


def install_homebrew() -> None:
    brew = _brew_path()
    shellenv_ok = _shellenv_configured()

    if brew is not None and shellenv_ok:
        console.print(
            f"[yellow]Homebrew already installed at {brew} and shellenv "
            f"wired in {_zprofile_path()} — skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        steps: list[str] = []
        if brew is None:
            steps.append(f"download {_INSTALL_SCRIPT_URL} and pipe into /bin/bash with NONINTERACTIVE=1")
        else:
            steps.append(f"keep existing brew at [dim]{brew}[/dim]")
        if not shellenv_ok:
            steps.append(
                f"append [dim]{_shellenv_line()}[/dim] to "
                f"[dim]{_zprofile_path()}[/dim]"
            )
        console.print("[cyan]DRY RUN[/cyan] would: " + "; ".join(steps) + ".")
        return

    if brew is None:
        console.print(
            "[bold]Installing Homebrew[/bold] — live output below "
            "(takes a few minutes)."
        )
        _install_brew()
        brew = _brew_path()
        if brew is None:
            console.print("[red]Homebrew installation finished but `brew` was not found on PATH or in the expected locations.[/red]")
            return
        console.print(f"[green]Homebrew installed at {brew}.[/green]")

    if not _shellenv_configured():
        _append_shellenv()
        console.print(
            f"[green]Wired brew shellenv into {_zprofile_path()}.[/green]"
        )
        console.print(
            "[dim]Open a new terminal (or run `source ~/.zprofile`) so "
            "`brew` lands on your PATH.[/dim]"
        )


module = Module(
    key="homebrew_install",
    title="Homebrew",
    description="Installs Homebrew (NONINTERACTIVE=1) and wires `brew shellenv` into ~/.zprofile.",
    run=install_homebrew,
)

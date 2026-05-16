from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import questionary

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run


@dataclass(frozen=True)
class Cask:
    name: str
    description: str


CASKS: list[Cask] = [
    Cask("iterm2", "Drop-in replacement for Terminal.app with panes, profiles, and search"),
]


def _brew_available() -> bool:
    return shutil.which("brew") is not None


def _is_installed(name: str) -> bool:
    result = subprocess.run(
        ["brew", "list", "--cask", "--versions", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and name in result.stdout


def install_casks() -> None:
    if not _brew_available():
        console.print(
            "[red]`brew` not found on PATH.[/red] Run the [bold]Homebrew[/bold] "
            "module first (or open a new terminal so `~/.zprofile` is sourced)."
        )
        return

    if runtime.dry_run:
        names = ", ".join(c.name for c in CASKS)
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt for selection among "
            f"[dim]{names}[/dim], then run [dim]brew install --cask <name>[/dim] "
            "for each selected cask (skipping ones already installed)."
        )
        return

    choices = [
        questionary.Choice(title=c.name, value=c.name, description=c.description)
        for c in CASKS
    ]
    selected = questionary.checkbox(
        "Pick casks (GUI apps) to install (space to toggle, enter to confirm):",
        choices=choices,
    ).ask()

    if not selected:
        console.print("[yellow]Nothing selected — exiting.[/yellow]")
        return

    for name in selected:
        if _is_installed(name):
            console.print(f"[yellow]{name} already installed — skipping.[/yellow]")
            continue
        console.rule(f"[bold]brew install --cask {name}[/bold]")
        result = mutating_run(["brew", "install", "--cask", name])
        if result.returncode != 0:
            console.print(f"[red]brew install --cask {name} failed (rc={result.returncode}).[/red]")
            if not questionary.confirm(
                "Continue with the remaining casks?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")


module = Module(
    key="homebrew_casks",
    title="Homebrew casks",
    description="Pick and install GUI apps (casks) from a curated list.",
    run=install_casks,
)

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
class Formula:
    name: str
    description: str


FORMULAE: list[Formula] = [
    Formula("mise", "Polyglot runtime/version manager (asdf successor — handles node/python/java/bun)"),
    Formula("gh", "GitHub CLI — auth, PRs, issues, gists from the terminal"),
]


def _brew_available() -> bool:
    return shutil.which("brew") is not None


def _is_installed(name: str) -> bool:
    result = subprocess.run(
        ["brew", "list", "--formula", "--versions", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and name in result.stdout


def _installed_set() -> set[str]:
    result = subprocess.run(
        ["brew", "list", "--formula", "--versions"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.split()[0] for line in result.stdout.splitlines() if line.split()}


def install_formulae() -> None:
    if not _brew_available():
        console.print(
            "[red]`brew` not found on PATH.[/red] Run the [bold]Homebrew[/bold] "
            "module first (or open a new terminal so `~/.zprofile` is sourced)."
        )
        return

    if runtime.dry_run:
        names = ", ".join(f.name for f in FORMULAE)
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt for selection among "
            f"[dim]{names}[/dim], then run [dim]brew install <name>[/dim] "
            "for each selected formula (skipping ones already installed)."
        )
        return

    installed = _installed_set()
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for f in FORMULAE:
        choices.append(
            questionary.Choice(
                title=f.name,
                value=f.name,
                description=f.description,
                disabled="installed" if f.name in installed else None,
            )
        )
    selected = questionary.checkbox(
        "Pick formulae to install (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
    ).ask()

    if not selected or "__back" in selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return
    selected = [s for s in selected if s != "__back"]

    for name in selected:
        if _is_installed(name):
            console.print(f"[yellow]{name} already installed — skipping.[/yellow]")
            continue
        console.rule(f"[bold]brew install {name}[/bold]")
        result = mutating_run(["brew", "install", name])
        if result.returncode != 0:
            console.print(f"[red]brew install {name} failed (rc={result.returncode}).[/red]")
            if not questionary.confirm(
                "Continue with the remaining formulae?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")


module = Module(
    key="homebrew_formulae",
    title="Homebrew formulae",
    description="Pick and install Homebrew formulae from a curated list.",
    run=install_formulae,
)

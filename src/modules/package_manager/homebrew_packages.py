from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Literal

import questionary

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run

Kind = Literal["formula", "cask"]


@dataclass(frozen=True)
class Package:
    name: str
    kind: Kind
    description: str


PACKAGES: list[Package] = [
    Package("brave-browser", "cask", "Brave — privacy-focused Chromium browser"),
    Package("the-unarchiver", "cask", "Archive utility for zip, rar, 7z, tar.gz"),
    Package("gh", "formula", "GitHub CLI — auth, PRs, issues, gists from the terminal"),
    Package("mise", "formula", "Polyglot runtime/version manager — handles node/python/java (asdf successor)"),
    Package("font-fira-code", "cask", "Fira Code monospace font with programming ligatures"),
    Package("docker-desktop", "cask", "Docker Desktop for Mac — containers + compose"),
    Package("iterm2", "cask", "Drop-in replacement for Terminal.app with panes, profiles, ligatures"),
    Package("visual-studio-code", "cask", "Microsoft Visual Studio Code — required for the Editor category"),
    Package("intellij-idea-ce", "cask", "IntelliJ IDEA Community Edition — JVM IDE"),
    Package("bruno", "cask", "API client — Git-friendly alternative to Postman"),
    Package("mockoon", "cask", "API mocking — design and run mock servers locally"),
    Package("beekeeper-studio", "cask", "SQL client for Postgres, MySQL, SQLite, SQL Server"),
    Package("bitwarden", "cask", "Password manager — desktop client"),
    Package("aldente", "cask", "Battery charge limiter — preserves battery health"),
    Package("betterdisplay", "cask", "Manage external displays, scaling, HiDPI modes"),
    Package("orka-desktop", "cask", "Orka Desktop — manage macOS VMs"),
]


def _brew_available() -> bool:
    return shutil.which("brew") is not None


def _installed_formulae() -> set[str]:
    result = subprocess.run(
        ["brew", "list", "--formula", "--versions"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.split()[0] for line in result.stdout.splitlines() if line.split()}


def _installed_casks() -> set[str]:
    result = subprocess.run(
        ["brew", "list", "--cask", "--versions"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.split()[0] for line in result.stdout.splitlines() if line.split()}


def _is_installed(pkg: Package, formulae: set[str], casks: set[str]) -> bool:
    if pkg.kind == "formula":
        return pkg.name in formulae
    return pkg.name in casks


def _install(pkg: Package) -> int:
    cmd = ["brew", "install"]
    if pkg.kind == "cask":
        cmd.append("--cask")
    cmd.append(pkg.name)
    console.rule(f"[bold]{' '.join(cmd)}[/bold]")
    result = mutating_run(cmd)
    return result.returncode


def install_homebrew_packages() -> None:
    if not _brew_available():
        console.print(
            "[red]`brew` not found on PATH.[/red] Run the [bold]Homebrew[/bold] "
            "module first (or open a new terminal so `~/.zprofile` is sourced)."
        )
        return

    if runtime.dry_run:
        formula_names = ", ".join(p.name for p in PACKAGES if p.kind == "formula")
        cask_names = ", ".join(p.name for p in PACKAGES if p.kind == "cask")
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt for selection among formulae "
            f"[dim]{formula_names}[/dim] and casks [dim]{cask_names}[/dim], then "
            "run [dim]brew install[/dim] (with [dim]--cask[/dim] when applicable) "
            "for each selected package (skipping ones already installed)."
        )
        return

    formulae = _installed_formulae()
    casks = _installed_casks()

    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for pkg in PACKAGES:
        suffix = " [cask]" if pkg.kind == "cask" else ""
        choices.append(
            questionary.Choice(
                title=f"{pkg.name}{suffix}",
                value=pkg.name,
                description=pkg.description,
                disabled="installed" if _is_installed(pkg, formulae, casks) else None,
            )
        )

    selected = questionary.checkbox(
        "Pick Homebrew packages to install (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
    ).ask()

    if not selected or "__back" in selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return
    selected_names = {s for s in selected if s != "__back"}

    by_name = {p.name: p for p in PACKAGES}
    for name in selected_names:
        pkg = by_name[name]
        rc = _install(pkg)
        if rc != 0:
            console.print(f"[red]brew install {name} failed (rc={rc}).[/red]")
            if not questionary.confirm(
                "Continue with the remaining packages?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")


module = Module(
    key="homebrew_packages",
    title="Homebrew packages",
    description="Pick formulae and casks from a single curated list (casks marked with [cask]).",
    run=install_homebrew_packages,
)

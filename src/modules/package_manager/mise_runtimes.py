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
class Runtime:
    title: str
    spec: str
    description: str


RUNTIMES: list[Runtime] = [
    Runtime("Node.js LTS", "node@lts", "Latest Node.js LTS release — installed and set as the global default"),
    Runtime("Bun latest", "bun@latest", "Bun runtime — rolling release, latest stable"),
    Runtime("Java LTS (Temurin 21)", "java@temurin-21", "Adoptium Temurin JDK 21 — current Java LTS"),
    Runtime("PHP 8.3", "php@8.3", "PHP 8.3 — current active branch (via mise/asdf-php plugin)"),
]


def _mise_available() -> bool:
    return shutil.which("mise") is not None


def _tool_from_spec(spec: str) -> str:
    return spec.split("@", 1)[0]


def _has_global(tool: str) -> bool:
    result = subprocess.run(
        ["mise", "current", tool],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def install_mise_runtimes() -> None:
    if not _mise_available():
        console.print(
            "[red]`mise` not found on PATH.[/red] Install it via "
            "[bold]Homebrew packages[/bold] (pick `mise`) and reopen the menu."
        )
        return

    if runtime.dry_run:
        specs = ", ".join(r.spec for r in RUNTIMES)
        console.print(
            f"[cyan]DRY RUN[/cyan] would query [dim]mise current <tool>[/dim] "
            f"for each of [dim]{specs}[/dim], prompt for selection, and run "
            "[dim]mise use -g <spec>[/dim] for each selected runtime."
        )
        return

    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for rt in RUNTIMES:
        already = _has_global(_tool_from_spec(rt.spec))
        choices.append(
            questionary.Choice(
                title=f"{rt.title}  [dim]({rt.spec})[/dim]",
                value=rt.spec,
                description=rt.description,
                disabled="installed (global)" if already else None,
            )
        )

    selected = questionary.checkbox(
        "Pick runtimes to install with mise (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
    ).ask()

    if not selected or "__back" in selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return
    selected = [s for s in selected if s != "__back"]

    for spec in selected:
        console.rule(f"[bold]mise use -g {spec}[/bold]")
        result = mutating_run(["mise", "use", "-g", spec])
        if result.returncode != 0:
            console.print(f"[red]mise use -g {spec} failed (rc={result.returncode}).[/red]")
            if not questionary.confirm(
                "Continue with the remaining runtimes?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")
    console.print(
        "[dim]Open a new shell (or run `mise activate zsh` in this one) so the "
        "runtimes land on PATH.[/dim]"
    )


module = Module(
    key="mise_runtimes",
    title="Mise runtimes",
    description="Install language runtimes via mise (Node.js LTS, Bun latest, Java LTS).",
    run=install_mise_runtimes,
)

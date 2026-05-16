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
    Runtime("Java LTS (Temurin 25)", "java@temurin-25", "Adoptium Temurin JDK 25 — current Java LTS (Sep 2025)"),
    Runtime("Maven latest", "maven@latest", "Apache Maven — JVM project management and build tool (requires Java)"),
    Runtime("Gradle latest", "gradle@latest", "Gradle — JVM and multi-language build tool (requires Java)"),
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


def _pick_action() -> str | None:
    answer = questionary.select(
        "Mise runtimes — what do you want to do?",
        choices=[
            questionary.Choice(title="Install", value="install"),
            questionary.Choice(title="Uninstall", value="uninstall"),
            questionary.Choice(title="← Back", value="__back"),
        ],
    ).ask()
    if answer in (None, "__back"):
        return None
    return answer


def _picker(action: str) -> list[str]:
    install_mode = action == "install"
    verb = "install" if install_mode else "uninstall"
    visible = [
        rt for rt in RUNTIMES
        if _has_global(_tool_from_spec(rt.spec)) != install_mode
    ]
    if not visible:
        empty_msg = (
            "All curated runtimes are already installed globally — nothing to install."
            if install_mode
            else "No curated runtimes are set globally right now — nothing to uninstall."
        )
        console.print(f"[yellow]{empty_msg}[/yellow]")
        return []
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for rt in visible:
        choices.append(
            questionary.Choice(
                title=f"{rt.title}  [dim]({rt.spec})[/dim]",
                value=rt.spec,
                description=rt.description,
            )
        )
    selected = questionary.checkbox(
        f"Pick runtimes to {verb} (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
    ).ask()
    if not selected or "__back" in selected:
        return []
    return [s for s in selected if s != "__back"]


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
            f"[cyan]DRY RUN[/cyan] would prompt Install/Uninstall, then over "
            f"[dim]{specs}[/dim] run [dim]mise use -g <spec>[/dim] or "
            "[dim]mise uninstall <spec>[/dim] for each selected runtime."
        )
        return

    action = _pick_action()
    if action is None:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    selected = _picker(action)
    if not selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    for spec in selected:
        if action == "install":
            cmd = ["mise", "use", "-g", spec]
        else:
            cmd = ["mise", "uninstall", spec]
        console.rule(f"[bold]{' '.join(cmd)}[/bold]")
        result = mutating_run(cmd)
        if result.returncode != 0:
            console.print(
                f"[red]{' '.join(cmd)} failed (rc={result.returncode}).[/red]"
            )
            if not questionary.confirm(
                f"Continue with the remaining {action}s?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")
    if action == "install":
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

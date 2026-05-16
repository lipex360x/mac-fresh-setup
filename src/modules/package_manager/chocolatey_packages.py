from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

import questionary

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run
from style import QUESTIONARY_STYLE


@dataclass(frozen=True)
class ChocoPackage:
    name: str
    description: str


PACKAGES: list[ChocoPackage] = [
    ChocoPackage("brave", "Brave — privacy-focused Chromium browser"),
    ChocoPackage("7zip", "7-Zip — archive utility for zip, rar, 7z, tar.gz"),
    ChocoPackage("gh", "GitHub CLI — auth, PRs, issues, gists from the terminal"),
    ChocoPackage("mise", "Polyglot runtime/version manager — handles node/python/java"),
    ChocoPackage("firacode", "Fira Code monospace font with programming ligatures"),
    ChocoPackage("microsoft-windows-terminal", "Windows Terminal — modern tabbed terminal app"),
    ChocoPackage("docker-desktop", "Docker Desktop for Windows — containers + compose"),
    ChocoPackage("vscode", "Microsoft Visual Studio Code — required for the Styling/VSCode stack"),
    ChocoPackage("intellijidea-community", "IntelliJ IDEA Community Edition — JVM IDE"),
    ChocoPackage("bruno", "API client — Git-friendly alternative to Postman"),
    ChocoPackage("mockoon", "API mocking — design and run mock servers locally"),
    ChocoPackage("beekeeper-studio", "SQL client for Postgres, MySQL, SQLite, SQL Server"),
    ChocoPackage("bitwarden", "Password manager — desktop client"),
]


def _choco_available() -> bool:
    return shutil.which("choco") is not None


def _installed_packages() -> set[str]:
    result = subprocess.run(
        ["choco", "list", "--limit-output"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    names: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        names.add(line.split("|", 1)[0].lower())
    return names


def _is_installed(pkg: ChocoPackage, installed: set[str]) -> bool:
    return pkg.name.lower() in installed


def _elevated_choco_cmd(action: str, names: list[str]) -> list[str]:
    args = ",".join([f"'{action}'", "'-y'"] + [f"'{n}'" for n in names])
    inner = f"Start-Process choco -Verb RunAs -Wait -ArgumentList {args}"
    return ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", inner]


def _run_batch(action: str, names: list[str]) -> int:
    cmd = _elevated_choco_cmd(action, names)
    console.rule(f"[bold]choco {action} -y {' '.join(names)}[/bold]")
    console.print(
        "[dim]A UAC prompt will appear — accept it. Choco runs in a separate "
        "elevated window and this script waits for it to finish.[/dim]"
    )
    result = mutating_run(cmd)
    return result.returncode


def _pick_action() -> str | None:
    answer = questionary.select(
        "Chocolatey packages — what do you want to do?",
        choices=[
            questionary.Choice(title="Install", value="install"),
            questionary.Choice(title="Uninstall", value="uninstall"),
            questionary.Choice(title="← Back", value="__back"),
        ],
        style=QUESTIONARY_STYLE,
    ).ask()
    if answer in (None, "__back"):
        return None
    return answer


def _picker(action: str, installed: set[str]) -> list[str]:
    install_mode = action == "install"
    title_verb = "install" if install_mode else "uninstall"
    visible = [
        pkg for pkg in PACKAGES
        if _is_installed(pkg, installed) != install_mode
    ]
    if not visible:
        empty_msg = (
            "Everything in the curated list is already installed — nothing to install."
            if install_mode
            else "No curated packages are installed right now — nothing to uninstall."
        )
        console.print(f"[yellow]{empty_msg}[/yellow]")
        return []
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for pkg in visible:
        choices.append(
            questionary.Choice(
                title=pkg.name,
                value=pkg.name,
                description=pkg.description,
            )
        )
    selected = questionary.checkbox(
        f"Pick Chocolatey packages to {title_verb} (space to toggle, enter to "
        "confirm — pick '← Back' alone to return):",
        choices=choices,
        style=QUESTIONARY_STYLE,
    ).ask()
    if not selected or "__back" in selected:
        return []
    return [s for s in selected if s != "__back"]


def install_chocolatey_packages() -> None:
    if not _choco_available():
        console.print(
            "[red]`choco` not found on PATH.[/red] Run the [bold]Chocolatey[/bold] "
            "module first, then open a new Git Bash window so choco lands on PATH."
        )
        return

    if runtime.dry_run:
        names = ", ".join(p.name for p in PACKAGES)
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt Install/Uninstall, then over "
            f"[dim]{names}[/dim] launch an elevated [dim]choco install -y[/dim] "
            "(or [dim]choco uninstall -y[/dim]) batched in a single UAC prompt."
        )
        return

    action = _pick_action()
    if action is None:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    installed = _installed_packages()
    selected_names = _picker(action, installed)
    if not selected_names:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    rc = _run_batch(action, selected_names)
    if rc != 0:
        console.print(
            f"[red]choco {action} batch exited with rc={rc}.[/red] "
            "If you cancelled UAC, re-run this module."
        )
        return

    console.rule("[bold green]Done[/bold green]")
    if action == "install":
        console.print(
            "[dim]Open a new Git Bash window so PATH picks up newly installed "
            "binaries.[/dim]"
        )


module = Module(
    key="chocolatey_packages",
    title="Chocolatey packages",
    description="Pick Windows packages from a curated list — batched elevated install via Chocolatey.",
    run=install_chocolatey_packages,
    platforms=frozenset({"win32"}),
)

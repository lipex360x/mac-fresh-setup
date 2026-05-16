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
class ScoopPackage:
    name: str
    description: str
    bucket: str = "main"


PACKAGES: list[ScoopPackage] = [
    ScoopPackage("7zip", "7-Zip — archive utility for zip, rar, 7z, tar.gz"),
    ScoopPackage("gh", "GitHub CLI — auth, PRs, issues, gists from the terminal"),
    ScoopPackage("mise", "Polyglot runtime/version manager — handles node/python/java"),
    ScoopPackage("brave", "Brave — privacy-focused Chromium browser", bucket="extras"),
    ScoopPackage("FiraCode-NF", "Fira Code Nerd Font — monospace + powerline glyphs", bucket="nerd-fonts"),
    ScoopPackage("windows-terminal", "Windows Terminal — modern tabbed terminal app", bucket="extras"),
    ScoopPackage("vscode", "Microsoft Visual Studio Code — required for the Styling/VSCode stack", bucket="extras"),
    ScoopPackage("idea-community", "IntelliJ IDEA Community Edition — JVM IDE", bucket="extras"),
    ScoopPackage("bruno", "API client — Git-friendly alternative to Postman", bucket="extras"),
    ScoopPackage("mockoon", "API mocking — design and run mock servers locally", bucket="extras"),
    ScoopPackage("beekeeper-studio", "SQL client for Postgres, MySQL, SQLite, SQL Server", bucket="extras"),
    ScoopPackage("bitwarden", "Password manager — desktop client", bucket="extras"),
    ScoopPackage("oh-my-posh", "Prompt theme engine — Windows analogue to Spaceship", bucket="extras"),
]

_REQUIRED_BUCKETS: dict[str, str] = {
    "extras": "https://github.com/ScoopInstaller/Extras",
    "nerd-fonts": "https://github.com/matthewjberger/scoop-nerd-fonts",
}


def _scoop_available() -> bool:
    return shutil.which("scoop") is not None


def _installed_packages() -> set[str]:
    result = subprocess.run(
        ["scoop", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    names: set[str] = set()
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("Name") or line.startswith("---"):
            continue
        if "Installed apps" in line or line.startswith("'"):
            continue
        parts = line.split()
        if not parts:
            continue
        names.add(parts[0].lower())
    return names


def _existing_buckets() -> set[str]:
    result = subprocess.run(
        ["scoop", "bucket", "list"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    names: set[str] = set()
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("Name") or line.startswith("---"):
            continue
        parts = line.split()
        if parts:
            names.add(parts[0].lower())
    return names


def _ensure_buckets(needed: set[str]) -> bool:
    if not needed:
        return True
    existing = _existing_buckets()
    missing = sorted(b for b in needed if b not in existing)
    for bucket in missing:
        repo = _REQUIRED_BUCKETS.get(bucket, "")
        cmd = ["scoop", "bucket", "add", bucket]
        if repo:
            cmd.append(repo)
        console.rule(f"[bold]{' '.join(cmd)}[/bold]")
        result = mutating_run(cmd)
        if result.returncode != 0:
            console.print(
                f"[red]Failed to add bucket `{bucket}` (rc={result.returncode}).[/red]"
            )
            return False
    return True


def _is_installed(pkg: ScoopPackage, installed: set[str]) -> bool:
    return pkg.name.lower() in installed


def _pick_action() -> str | None:
    answer = questionary.select(
        "Scoop packages — what do you want to do?",
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


def _picker(action: str, installed: set[str]) -> list[ScoopPackage]:
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
    by_name = {p.name: p for p in visible}
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for pkg in visible:
        suffix = "" if pkg.bucket == "main" else f"  [{pkg.bucket}]"
        choices.append(
            questionary.Choice(
                title=f"{pkg.name}{suffix}",
                value=pkg.name,
                description=pkg.description,
            )
        )
    selected = questionary.checkbox(
        f"Pick Scoop packages to {title_verb} (space to toggle, enter to "
        "confirm — pick '← Back' alone to return):",
        choices=choices,
        style=QUESTIONARY_STYLE,
    ).ask()
    if not selected or "__back" in selected:
        return []
    return [by_name[s] for s in selected if s != "__back"]


def install_scoop_packages() -> None:
    if not _scoop_available():
        console.print(
            "[red]`scoop` not found on PATH.[/red] Run the [bold]Scoop[/bold] "
            "module first, then open a new Git Bash window so scoop lands on PATH."
        )
        return

    if runtime.dry_run:
        names = ", ".join(p.name for p in PACKAGES)
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt Install/Uninstall, then over "
            f"[dim]{names}[/dim] run [dim]scoop install[/dim] / "
            "[dim]scoop uninstall[/dim] (auto-adding the `extras` and "
            "`nerd-fonts` buckets when needed). No admin / no UAC."
        )
        return

    action = _pick_action()
    if action is None:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    installed = _installed_packages()
    selected = _picker(action, installed)
    if not selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    if action == "install":
        buckets = {p.bucket for p in selected if p.bucket != "main"}
        if not _ensure_buckets(buckets):
            return

    names = [p.name for p in selected]
    cmd = ["scoop", action, *names]
    console.rule(f"[bold]{' '.join(cmd)}[/bold]")
    result = mutating_run(cmd)
    if result.returncode != 0:
        console.print(
            f"[red]scoop {action} batch exited with rc={result.returncode}.[/red]"
        )
        return

    console.rule("[bold green]Done[/bold green]")
    if action == "install":
        console.print(
            "[dim]Open a new Git Bash window so PATH picks up newly installed "
            "binaries.[/dim]"
        )


module = Module(
    key="scoop_packages",
    title="Scoop packages",
    description="Pick Windows packages from a curated list — user-level install via Scoop, no admin / no UAC.",
    run=install_scoop_packages,
    platforms=frozenset({"win32"}),
)

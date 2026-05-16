from __future__ import annotations

import argparse
import shutil
import sys

import questionary
from rich.panel import Panel

from categories import CATEGORIES
from console import console
from models import Category, Module
from modules.system.git_for_windows import git_present as _windows_git_present
from modules.system.git_for_windows import module as _git_for_windows_module
from runtime import runtime
from style import QUESTIONARY_STYLE


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="os-fresh-setup",
        description="Interactive bootstrap for a fresh OS install (macOS / Linux / Windows).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what each module would do without making any changes.",
    )
    return parser.parse_args(argv)


def _preflight() -> None:
    if sys.platform not in {"darwin", "linux", "win32"}:
        console.print(f"[red]Unsupported platform: {sys.platform}[/red]")
        sys.exit(1)
    if sys.platform == "darwin":
        for binary in ("sudo", "ssh-keygen"):
            if shutil.which(binary) is None:
                console.print(f"[red]Required binary not found in PATH: {binary}[/red]")
                sys.exit(1)


def _supported_modules(category: Category) -> tuple[Module, ...]:
    return tuple(m for m in category.modules if sys.platform in m.platforms)


def _supported_categories() -> list[Category]:
    if sys.platform == "win32" and not _windows_git_present():
        return [
            Category(
                key="system",
                title="System",
                modules=(_git_for_windows_module,),
            )
        ]
    return [c for c in CATEGORIES if _supported_modules(c)]


def _run_module(module: Module) -> None:
    console.rule(f"[bold]{module.title}[/bold]")
    try:
        module.run()
    except Exception as exc:
        console.print(f"[red]Module {module.key} failed: {exc}[/red]")
    console.print()
    questionary.press_any_key_to_continue(
        "Press any key to return to the menu...",
        style=QUESTIONARY_STYLE,
    ).ask()


def _category_menu(category: Category) -> None:
    while True:
        modules = _supported_modules(category)
        choices = [questionary.Choice(title=m.title, value=m.key) for m in modules]
        choices.append(questionary.Choice(title="← Back", value="__back"))
        answer = questionary.select(
            f"{category.title} — pick a module:",
            choices=choices,
            style=QUESTIONARY_STYLE,
        ).ask()
        if answer in (None, "__back"):
            return
        module = next(m for m in modules if m.key == answer)
        _run_module(module)


def run(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    runtime.dry_run = args.dry_run
    _preflight()
    banner = (
        "[bold cyan]OS Fresh Setup[/bold cyan]\n"
        "Interactive bootstrap for a fresh install (macOS / Linux / Windows)."
    )
    if runtime.dry_run:
        banner += "\n[bold yellow]DRY RUN — no changes will be made.[/bold yellow]"
    console.print(Panel.fit(banner, border_style="cyan"))

    while True:
        categories = _supported_categories()
        choices = [questionary.Choice(title=c.title, value=c.key) for c in categories]
        choices.append(questionary.Choice(title="Exit", value="__exit"))
        answer = questionary.select(
            "Pick a category:",
            choices=choices,
            style=QUESTIONARY_STYLE,
        ).ask()
        if answer in (None, "__exit"):
            console.rule("[bold green]Bye[/bold green]")
            return
        category = next(c for c in categories if c.key == answer)
        _category_menu(category)

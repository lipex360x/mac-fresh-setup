from __future__ import annotations

import argparse
import shutil
import sys

import questionary
from rich.panel import Panel

from categories import CATEGORIES
from console import console
from models import Category, Module
from runtime import runtime


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mac-fresh-setup",
        description="Interactive bootstrap for a fresh macOS install.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what each module would do without making any changes.",
    )
    return parser.parse_args(argv)


def _preflight() -> None:
    if sys.platform != "darwin":
        console.print("[red]This script targets macOS only.[/red]")
        sys.exit(1)
    for binary in ("sudo", "ssh-keygen"):
        if shutil.which(binary) is None:
            console.print(f"[red]Required binary not found in PATH: {binary}[/red]")
            sys.exit(1)


def _run_module(module: Module) -> None:
    console.rule(f"[bold]{module.title}[/bold]")
    try:
        module.run()
    except Exception as exc:
        console.print(f"[red]Module {module.key} failed: {exc}[/red]")
    console.print()
    questionary.press_any_key_to_continue("Press any key to return to the menu...").ask()


def _category_menu(category: Category) -> None:
    while True:
        choices = [questionary.Choice(title=m.title, value=m.key) for m in category.modules]
        choices.append(questionary.Choice(title="← Back", value="__back"))
        answer = questionary.select(
            f"{category.title} — pick a module:",
            choices=choices,
        ).ask()
        if answer in (None, "__back"):
            return
        module = next(m for m in category.modules if m.key == answer)
        _run_module(module)


def run(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    runtime.dry_run = args.dry_run
    _preflight()
    banner = (
        "[bold cyan]mac-fresh-setup[/bold cyan]\n"
        "Interactive bootstrap for a fresh macOS install."
    )
    if runtime.dry_run:
        banner += "\n[bold yellow]DRY RUN — no changes will be made.[/bold yellow]"
    console.print(Panel.fit(banner, border_style="cyan"))

    while True:
        choices = [questionary.Choice(title=c.title, value=c.key) for c in CATEGORIES]
        choices.append(questionary.Choice(title="Exit", value="__exit"))
        answer = questionary.select(
            "Pick a category:",
            choices=choices,
        ).ask()
        if answer in (None, "__exit"):
            console.rule("[bold green]Bye[/bold green]")
            return
        category = next(c for c in CATEGORIES if c.key == answer)
        _category_menu(category)

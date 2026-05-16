from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import questionary

from console import console
from models import Module
from modules.editor._code_cli import code_binary
from runtime import runtime
from safe import mutating_run


@dataclass(frozen=True)
class Extension:
    extension_id: str
    description: str


EXTENSIONS: list[Extension] = [
    Extension("dbaeumer.vscode-eslint", "ESLint integration for JavaScript/TypeScript"),
    Extension("esbenp.prettier-vscode", "Prettier — code formatter"),
    Extension("eamodio.gitlens", "GitLens — supercharge Git inside VSCode"),
    Extension("github.copilot", "GitHub Copilot — AI pair programmer"),
    Extension("github.copilot-chat", "GitHub Copilot Chat — in-editor AI conversations"),
    Extension("ms-azuretools.vscode-docker", "Docker — manage containers, images and compose"),
    Extension("ms-python.python", "Python — language support, debugger, REPL"),
    Extension("redhat.java", "Java — language support by Red Hat"),
    Extension("oven.bun-vscode", "Bun — language and debugger support"),
    Extension("editorconfig.editorconfig", "EditorConfig — respects .editorconfig files"),
    Extension("usernamehw.errorlens", "Error Lens — inline diagnostics next to code"),
]


def _installed_set(code_bin: Path) -> set[str]:
    result = subprocess.run(
        [str(code_bin), "--list-extensions"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return set()
    return {line.strip().lower() for line in result.stdout.splitlines() if line.strip()}


def install_vscode_extensions() -> None:
    code_bin = code_binary()
    if code_bin is None:
        console.print(
            "[red]VSCode `code` CLI not found.[/red] Install the "
            "[bold]visual-studio-code[/bold] cask first (Package manager → "
            "Homebrew casks), or run [dim]Cmd+Shift+P → "
            "Shell Command: Install 'code' command in PATH[/dim] inside VSCode."
        )
        return

    if runtime.dry_run:
        ids = ", ".join(e.extension_id for e in EXTENSIONS)
        console.print(
            f"[cyan]DRY RUN[/cyan] would query [dim]{code_bin} --list-extensions[/dim], "
            f"prompt for selection among [dim]{ids}[/dim], then run "
            f"[dim]{code_bin.name} --install-extension <id>[/dim] for each selected."
        )
        return

    installed = _installed_set(code_bin)
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for ext in EXTENSIONS:
        choices.append(
            questionary.Choice(
                title=ext.extension_id,
                value=ext.extension_id,
                description=ext.description,
                disabled="installed" if ext.extension_id.lower() in installed else None,
            )
        )

    selected = questionary.checkbox(
        "Pick VSCode extensions to install (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
    ).ask()

    if not selected or "__back" in selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return
    selected = [s for s in selected if s != "__back"]

    for ext_id in selected:
        console.rule(f"[bold]code --install-extension {ext_id}[/bold]")
        result = mutating_run([str(code_bin), "--install-extension", ext_id])
        if result.returncode != 0:
            console.print(
                f"[red]Failed to install {ext_id} (rc={result.returncode}).[/red]"
            )
            if not questionary.confirm(
                "Continue with the remaining extensions?", default=True
            ).ask():
                return

    console.rule("[bold green]Done[/bold green]")


module = Module(
    key="vscode_extensions",
    title="VSCode extensions",
    description="Pick and install curated VSCode extensions via `code --install-extension`.",
    run=install_vscode_extensions,
)

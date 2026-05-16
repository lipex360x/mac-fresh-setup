#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "questionary>=2.0",
#     "rich>=13.7",
# ]
# ///
"""mac-fresh-setup — interactive bootstrap for a fresh macOS install."""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()


@dataclass(frozen=True)
class Module:
    key: str
    title: str
    description: str
    run: Callable[[], None]


def _run(cmd: list[str], *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        input=input_text,
        capture_output=True,
    )


def grant_root_access() -> None:
    user = getpass.getuser()
    sudoers_path = Path(f"/etc/sudoers.d/{user}")
    expected_line = f"{user} ALL=(ALL) NOPASSWD:ALL"

    if sudoers_path.exists():
        try:
            content = subprocess.run(
                ["sudo", "cat", str(sudoers_path)],
                check=True,
                text=True,
                capture_output=True,
            ).stdout
        except subprocess.CalledProcessError as exc:
            console.print(f"[red]Failed to read {sudoers_path}: {exc.stderr}[/red]")
            raise
        if expected_line in content:
            console.print(f"[yellow]sudoers already configured for {user} — skipping.[/yellow]")
            return

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sudoers") as tmp:
        tmp.write(expected_line + "\n")
        tmp_path = Path(tmp.name)

    try:
        validation = subprocess.run(
            ["sudo", "visudo", "-cf", str(tmp_path)],
            text=True,
            capture_output=True,
        )
        if validation.returncode != 0:
            console.print(f"[red]visudo validation failed:[/red] {validation.stderr}")
            raise RuntimeError("invalid sudoers content")

        subprocess.run(
            ["sudo", "install", "-m", "0440", "-o", "root", "-g", "wheel", str(tmp_path), str(sudoers_path)],
            check=True,
        )
        console.print(f"[green]Sudoers rule installed at {sudoers_path}.[/green]")
    finally:
        tmp_path.unlink(missing_ok=True)


def generate_ssh_key() -> None:
    ssh_dir = Path.home() / ".ssh"
    private_key = ssh_dir / "id_rsa"
    public_key = ssh_dir / "id_rsa.pub"

    if private_key.exists():
        console.print(f"[yellow]SSH key already exists at {private_key} — skipping generation.[/yellow]")
    else:
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        email = questionary.text(
            "Email for the SSH key comment (used to identify the key on GitHub):",
            default=os.environ.get("GIT_EMAIL", ""),
        ).ask()
        if email is None:
            console.print("[red]Aborted.[/red]")
            return

        console.print(Panel.fit(
            "[bold]ssh-keygen will prompt for a passphrase next.[/bold]\n"
            "Leave it empty for no passphrase, or type one and confirm it.",
            border_style="cyan",
        ))
        result = subprocess.run(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email, "-f", str(private_key)],
        )
        if result.returncode != 0:
            console.print("[red]ssh-keygen failed.[/red]")
            return

    private_key.chmod(0o400)
    if public_key.exists():
        console.print(Panel(
            public_key.read_text().strip(),
            title=f"[bold green]Public key ({public_key})[/bold green]",
            subtitle="copy this into GitHub → Settings → SSH and GPG keys",
            border_style="green",
        ))


MODULES: list[Module] = [
    Module(
        key="sudoers",
        title="Grant Root Access (sudoers NOPASSWD)",
        description="Adds the current user to /etc/sudoers.d with NOPASSWD.",
        run=grant_root_access,
    ),
    Module(
        key="ssh_key",
        title="SSH Key (RSA 4096)",
        description="Generates ~/.ssh/id_rsa if missing and prints the public key.",
        run=generate_ssh_key,
    ),
]


def preflight() -> None:
    if sys.platform != "darwin":
        console.print("[red]This script targets macOS only.[/red]")
        sys.exit(1)
    for binary in ("sudo", "ssh-keygen"):
        if shutil.which(binary) is None:
            console.print(f"[red]Required binary not found in PATH: {binary}[/red]")
            sys.exit(1)


def main() -> None:
    preflight()
    console.print(Panel.fit(
        "[bold cyan]mac-fresh-setup[/bold cyan]\n"
        "Interactive bootstrap for a fresh macOS install.",
        border_style="cyan",
    ))

    choices = [
        questionary.Choice(title=f"{m.title} — {m.description}", value=m.key, checked=True)
        for m in MODULES
    ]
    selected = questionary.checkbox(
        "Select the modules to run (space to toggle, enter to confirm):",
        choices=choices,
    ).ask()

    if not selected:
        console.print("[yellow]Nothing selected — exiting.[/yellow]")
        return

    by_key = {m.key: m for m in MODULES}
    for key in selected:
        module = by_key[key]
        console.rule(f"[bold]{module.title}[/bold]")
        try:
            module.run()
        except Exception as exc:
            console.print(f"[red]Module {module.key} failed: {exc}[/red]")
            if not questionary.confirm("Continue with the remaining modules?", default=False).ask():
                sys.exit(1)

    console.rule("[bold green]Done[/bold green]")


if __name__ == "__main__":
    main()

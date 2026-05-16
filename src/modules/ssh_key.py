from __future__ import annotations

import os
import subprocess
from pathlib import Path

import questionary
from rich.panel import Panel

from console import console
from models import Module


def generate_ssh_key() -> None:
    ssh_dir = Path.home() / ".ssh"
    private_key = ssh_dir / "id_rsa"
    public_key = ssh_dir / "id_rsa.pub"

    if private_key.exists():
        console.print(
            f"[yellow]SSH key already exists at {private_key} — skipping generation.[/yellow]"
        )
    else:
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        email = questionary.text(
            "Email for the SSH key comment (used to identify the key on GitHub):",
            default=os.environ.get("GIT_EMAIL", ""),
        ).ask()
        if email is None:
            console.print("[red]Aborted.[/red]")
            return

        console.print(
            Panel.fit(
                "[bold]ssh-keygen will prompt for a passphrase next.[/bold]\n"
                "Leave it empty for no passphrase, or type one and confirm it.",
                border_style="cyan",
            )
        )
        result = subprocess.run(
            ["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email, "-f", str(private_key)],
        )
        if result.returncode != 0:
            console.print("[red]ssh-keygen failed.[/red]")
            return

    private_key.chmod(0o400)
    if public_key.exists():
        console.print(
            Panel(
                public_key.read_text().strip(),
                title=f"[bold green]Public key ({public_key})[/bold green]",
                subtitle="copy this into GitHub → Settings → SSH and GPG keys",
                border_style="green",
            )
        )


module = Module(
    key="ssh_key",
    title="SSH Key",
    description="Generates ~/.ssh/id_rsa if missing and prints the public key.",
    run=generate_ssh_key,
)

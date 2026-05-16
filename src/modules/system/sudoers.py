from __future__ import annotations

import getpass
import subprocess
import tempfile
from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_run


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
            console.print(f"[yellow]Sudoers already configured for {user} — skipping.[/yellow]")
            return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would write:\n  [dim]{expected_line}[/dim]\n"
            f"to [dim]{sudoers_path}[/dim] (mode 0440, owner root:wheel) "
            f"after [dim]visudo -cf[/dim] validation."
        )
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

        mutating_run(
            [
                "sudo",
                "install",
                "-m",
                "0440",
                "-o",
                "root",
                "-g",
                "wheel",
                str(tmp_path),
                str(sudoers_path),
            ],
            check=True,
        )
        console.print(f"[green]Sudoers rule installed at {sudoers_path}.[/green]")
    finally:
        tmp_path.unlink(missing_ok=True)


module = Module(
    key="sudoers",
    title="Grant Root Access",
    description="Adds the current user to /etc/sudoers.d with NOPASSWD.",
    run=grant_root_access,
)

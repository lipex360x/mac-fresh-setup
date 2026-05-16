from __future__ import annotations

from console import console
from models import Module
from modules.styling import oh_my_zsh, spaceship, zshrc


def install_zsh_stack() -> None:
    console.rule("[bold cyan]1/3 — Oh-my-zsh[/bold cyan]")
    oh_my_zsh.install_oh_my_zsh()
    console.rule("[bold cyan]2/3 — Spaceship theme[/bold cyan]")
    spaceship.install_spaceship()
    console.rule("[bold cyan]3/3 — Custom .zshrc[/bold cyan]")
    zshrc.sync_zshrc()
    console.rule("[bold green]Zsh stack ready[/bold green]")


module = Module(
    key="zsh_stack",
    title="Zsh stack (OMZ + Spaceship + .zshrc)",
    description="Runs Oh-my-zsh, Spaceship theme, and the bundled .zshrc sync in one go.",
    run=install_zsh_stack,
    platforms=frozenset({"darwin", "linux"}),
)

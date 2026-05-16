from __future__ import annotations

from pathlib import Path

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_OMZ_CUSTOM = Path.home() / ".oh-my-zsh" / "custom"
_SPACESHIP_DIR = _OMZ_CUSTOM / "themes" / "spaceship-prompt"
_SPACESHIP_THEME_LINK = _OMZ_CUSTOM / "themes" / "spaceship.zsh-theme"
_SPACESHIP_REPO = "https://github.com/denysdovhan/spaceship-prompt.git"


def _omz_present() -> bool:
    return (Path.home() / ".oh-my-zsh" / "oh-my-zsh.sh").is_file()


def _spaceship_installed() -> bool:
    return _SPACESHIP_DIR.is_dir() and _SPACESHIP_THEME_LINK.is_symlink()


def install_spaceship() -> None:
    if not _omz_present():
        console.print(
            "[red]Oh-my-zsh not found.[/red] Run the [bold]Oh-my-zsh[/bold] module "
            "first."
        )
        return

    if _spaceship_installed():
        console.print(
            f"[yellow]Spaceship already installed at {_SPACESHIP_DIR} — "
            "skipping.[/yellow]"
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would clone [dim]{_SPACESHIP_REPO}[/dim] into "
            f"[dim]{_SPACESHIP_DIR}[/dim] (depth 1) and symlink "
            f"[dim]{_SPACESHIP_THEME_LINK}[/dim] → "
            f"[dim]{_SPACESHIP_DIR}/spaceship.zsh-theme[/dim]."
        )
        return

    mutating_check(f"clone spaceship-prompt into {_SPACESHIP_DIR}")
    _SPACESHIP_DIR.parent.mkdir(parents=True, exist_ok=True)

    if not _SPACESHIP_DIR.is_dir():
        result = mutating_run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                _SPACESHIP_REPO,
                str(_SPACESHIP_DIR),
            ],
        )
        if result.returncode != 0:
            console.print(
                f"[red]git clone failed (rc={result.returncode}).[/red]"
            )
            return

    if not _SPACESHIP_THEME_LINK.is_symlink():
        mutating_check(f"symlink {_SPACESHIP_THEME_LINK}")
        _SPACESHIP_THEME_LINK.symlink_to(_SPACESHIP_DIR / "spaceship.zsh-theme")

    console.print(
        f"[green]Spaceship installed at {_SPACESHIP_DIR}.[/green]\n"
        "[dim]Make sure `ZSH_THEME=\"spaceship\"` is set in ~/.zshrc "
        "(the bundled zshrc module sets it).[/dim]"
    )


module = Module(
    key="spaceship",
    title="Spaceship theme",
    description="Clones denysdovhan/spaceship-prompt under $ZSH_CUSTOM/themes and symlinks the theme file.",
    run=install_spaceship,
)

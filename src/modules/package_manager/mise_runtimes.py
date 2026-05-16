from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import questionary

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run
from style import QUESTIONARY_STYLE

_SHIMS_LINE_BASH = (
    '[ -d "$HOME/AppData/Local/Mise/shims" ] && '
    'export PATH="$HOME/AppData/Local/Mise/shims:$PATH"'
)
_ACTIVATE_LINE_BASH = 'command -v mise >/dev/null && eval "$(mise activate bash)"'


@dataclass(frozen=True)
class Runtime:
    title: str
    spec: str
    description: str


RUNTIMES: list[Runtime] = [
    Runtime("Node.js LTS", "node@lts", "Latest Node.js LTS release — installed and set as the global default"),
    Runtime("Bun latest", "bun@latest", "Bun runtime — rolling release, latest stable"),
    Runtime("Java 21 LTS (Temurin)", "java@temurin-21.0.11+10.0.LTS", "Adoptium Temurin JDK 21 LTS — current LTS in the mise registry (Java 25 LTS not yet packaged)"),
    Runtime("Maven latest", "maven@latest", "Apache Maven — JVM project management and build tool (requires Java)"),
    Runtime("Gradle latest", "gradle@latest", "Gradle — JVM and multi-language build tool (requires Java)"),
]


def _mise_available() -> bool:
    return shutil.which("mise") is not None


def _mise_cmd(args: list[str]) -> list[str]:
    """Build a subprocess argv that invokes mise.

    On Windows mise is delivered as a `.cmd` shim (Scoop) or `.exe` — Python's
    CreateProcess only auto-resolves `.exe`. Prefix with `cmd /c` so the
    `.cmd` form is found by name.
    """
    base = ["mise", *args]
    if sys.platform == "win32":
        return ["cmd", "/c", *base]
    return base


def _tool_from_spec(spec: str) -> str:
    return spec.split("@", 1)[0]


def _is_installed(spec: str) -> bool:
    """Check whether the actual runtime files for `spec` are on disk.

    `mise where <spec>` returns the install path on success and a non-zero
    rc when the version is not installed (regardless of whether the global
    config still pins it). This is the source of truth — `mise current`
    only checks the pin, which leaves stale entries after `mise uninstall`.
    """
    result = subprocess.run(
        _mise_cmd(["where", spec]),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _pick_action() -> str | None:
    answer = questionary.select(
        "Mise runtimes — what do you want to do?",
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


def _picker(action: str) -> list[str]:
    install_mode = action == "install"
    verb = "install" if install_mode else "uninstall"
    visible = [
        rt for rt in RUNTIMES
        if _is_installed(rt.spec) != install_mode
    ]
    if not visible:
        empty_msg = (
            "All curated runtimes are already installed globally — nothing to install."
            if install_mode
            else "No curated runtimes are set globally right now — nothing to uninstall."
        )
        console.print(f"[yellow]{empty_msg}[/yellow]")
        return []
    choices: list[questionary.Choice] = [
        questionary.Choice(title="← Back", value="__back"),
    ]
    for rt in visible:
        choices.append(
            questionary.Choice(
                title=f"{rt.title}  ({rt.spec})",
                value=rt.spec,
                description=rt.description,
            )
        )
    selected = questionary.checkbox(
        f"Pick runtimes to {verb} (space to toggle, enter to confirm — "
        "pick '← Back' alone to return):",
        choices=choices,
        style=QUESTIONARY_STYLE,
    ).ask()
    if not selected or "__back" in selected:
        return []
    return [s for s in selected if s != "__back"]


def _ensure_mise_activate_on_windows() -> None:
    """Wire mise into Git Bash on Windows.

    Two lines, each appended only if missing:

    1. Explicit shims PATH export. `mise activate bash` on Windows
       (mise installed via Scoop) does NOT add the shims directory to
       PATH — it only puts mise.exe itself on PATH. Without this line,
       `mise use -g bun@latest` installs bun successfully but `bun
       --version` returns "command not found" in any new shell.

    2. `eval "$(mise activate bash)"` for the `mise()` shell function
       and the chpwd hook (auto-detects mise.toml in project dirs).
       Not load-bearing for the bun-on-PATH problem but still useful.

    Mac/Linux users get the equivalent through the bundled Zsh stack's
    .zshrc; this helper is a no-op on those platforms.
    """
    if sys.platform != "win32":
        return
    bashrc = Path.home() / ".bashrc"
    existing = bashrc.read_text() if bashrc.exists() else ""
    needs_shims = _SHIMS_LINE_BASH not in existing
    needs_activate = _ACTIVATE_LINE_BASH not in existing
    if not needs_shims and not needs_activate:
        return

    missing: list[str] = []
    if needs_shims:
        missing.append(_SHIMS_LINE_BASH)
    if needs_activate:
        missing.append(_ACTIVATE_LINE_BASH)

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would append the following to [dim]{bashrc}[/dim]:"
        )
        for line in missing:
            console.print(f"  [dim]{line}[/dim]")
        return

    mutating_check(f"append mise PATH+activate to {bashrc}")
    if existing and not existing.endswith("\n"):
        existing += "\n"
    block = "\n### mise shims (PATH) and activate (shell function + chpwd hook)\n"
    block += "\n".join(missing) + "\n"
    bashrc.write_text(existing + block)
    console.print(
        f"[green]Wired mise shims PATH and activate into {bashrc}.[/green] "
        "Run [dim]exec bash -l[/dim] (or open a new Git Bash window) so the "
        "shims show up on PATH."
    )


def install_mise_runtimes() -> None:
    if not _mise_available():
        installer = (
            "[bold]Scoop packages[/bold] (pick `mise`)"
            if sys.platform == "win32"
            else "[bold]Homebrew packages[/bold] (pick `mise`)"
        )
        console.print(
            f"[red]`mise` not found on PATH.[/red] Install it via {installer} "
            "and reopen the menu."
        )
        return

    _ensure_mise_activate_on_windows()

    if runtime.dry_run:
        specs = ", ".join(r.spec for r in RUNTIMES)
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt Install/Uninstall, then over "
            f"[dim]{specs}[/dim] run [dim]mise use -g <spec>[/dim] or "
            "[dim]mise uninstall <spec>[/dim] for each selected runtime."
        )
        return

    action = _pick_action()
    if action is None:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    selected = _picker(action)
    if not selected:
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    for spec in selected:
        if action == "install":
            steps = [_mise_cmd(["use", "-g", spec])]
        else:
            tool = _tool_from_spec(spec)
            steps = [_mise_cmd(["uninstall", spec]), _mise_cmd(["unuse", "-g", tool])]
        for cmd in steps:
            console.rule(f"[bold]{' '.join(cmd)}[/bold]")
            result = mutating_run(cmd)
            if result.returncode != 0:
                console.print(
                    f"[red]{' '.join(cmd)} failed (rc={result.returncode}).[/red]"
                )
                if not questionary.confirm(
                    f"Continue with the remaining {action}s?",
                    default=True,
                    style=QUESTIONARY_STYLE,
                ).ask():
                    return
                break

    console.rule("[bold green]Done[/bold green]")
    if action == "install":
        shell_name = "zsh" if sys.platform == "darwin" else "bash"
        console.print(
            f"[dim]Open a new shell (or run `mise activate {shell_name}` in this one) "
            "so the runtimes land on PATH.[/dim]"
        )


module = Module(
    key="mise_runtimes",
    title="Mise runtimes",
    description="Install language runtimes via mise (Node.js LTS, Bun latest, Java LTS).",
    run=install_mise_runtimes,
)

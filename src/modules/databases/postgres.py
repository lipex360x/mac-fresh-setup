from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Literal

import questionary
from rich.panel import Panel

from console import console
from models import Module
from runtime import runtime
from safe import mutating_check, mutating_run

_PG_VERSION = "17.4"
_PG_REV = "1"
_DEFAULT_PORT = 5432

_ROOT = Path.home() / ".local" / "share" / "mac-fresh-setup" / "postgres"
_INSTALLS = _ROOT / "installs"
_DATA = _ROOT / "data"
_RUNTIME = _ROOT / "runtime"
_CONFIG_PATH = _ROOT / "config.json"
_BIN_DIR = Path.home() / ".local" / "bin"
_WRAPPER_NAMES = ("postgres-up", "postgres-down", "postgres-status", "postgres-cli")
_REPO_WRAPPER_DIR = Path(__file__).resolve().parents[3] / "config" / "postgres" / "wrappers"


def _platform_slug() -> str:
    if sys.platform == "darwin":
        return "osx"
    if sys.platform == "win32":
        return "windows-x64"
    return "linux-x64"


def _archive_name() -> str:
    return f"postgresql-{_PG_VERSION}-{_PG_REV}-{_platform_slug()}-binaries.zip"


def _tarball_url() -> str:
    return f"https://get.enterprisedb.com/postgresql/{_archive_name()}"


def _install_dir() -> Path:
    return _INSTALLS / _PG_VERSION / "pgsql"


def _binaries_present() -> bool:
    return (_install_dir() / "bin" / "initdb").exists()


def _load_config() -> dict | None:
    if not _CONFIG_PATH.exists():
        return None
    return json.loads(_CONFIG_PATH.read_text())


def _save_config(cfg: dict) -> None:
    _ROOT.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    _CONFIG_PATH.chmod(0o600)


def _pid_running() -> bool:
    import os
    pid_file = _DATA / "postmaster.pid"
    if not pid_file.exists():
        return False
    try:
        first_line = pid_file.read_text().splitlines()[0].strip()
        pid = int(first_line)
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, IndexError):
        return False


def _state() -> Literal["not-installed", "running", "stopped"]:
    if not _binaries_present():
        return "not-installed"
    return "running" if _pid_running() else "stopped"


def _copy_wrappers() -> None:
    mutating_check(f"copy PostgreSQL wrappers to {_BIN_DIR}")
    _BIN_DIR.mkdir(parents=True, exist_ok=True)
    for name in _WRAPPER_NAMES:
        src = _REPO_WRAPPER_DIR / name
        dst = _BIN_DIR / name
        shutil.copyfile(src, dst)
        dst.chmod(0o755)


def _remove_wrappers() -> None:
    mutating_check(f"remove PostgreSQL wrappers from {_BIN_DIR}")
    for name in _WRAPPER_NAMES:
        (_BIN_DIR / name).unlink(missing_ok=True)


def _download_and_extract() -> None:
    url = _tarball_url()
    console.print(f"[dim]Downloading {url}[/dim]")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        archive = Path(tmp.name)
    try:
        rc = mutating_run(
            ["curl", "-fL", "--progress-bar", "-o", str(archive), url]
        ).returncode
        if rc != 0:
            raise RuntimeError(f"curl exited with {rc}")
        target = _INSTALLS / _PG_VERSION
        target.mkdir(parents=True, exist_ok=True)
        console.print(f"[dim]Extracting to {target}...[/dim]")
        _extract_zip_preserving_perms(archive, target)
    finally:
        archive.unlink(missing_ok=True)


def _extract_zip_preserving_perms(archive: Path, target: Path) -> None:
    """Extract a ZIP preserving Unix mode bits.

    Python's zipfile.extractall drops the executable bit, which leaves
    EDB's bin/ binaries non-runnable. We replay the mode from the
    ZIP entry's external_attr (upper 16 bits) after each extract.
    """
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            extracted = Path(zf.extract(info, target))
            mode = info.external_attr >> 16
            if mode:
                extracted.chmod(mode & 0o7777)


def _do_install() -> None:
    if _binaries_present():
        console.print(
            f"[yellow]Binaries already at {_install_dir()} — skipping download.[/yellow]"
        )
    else:
        _download_and_extract()
        if not _binaries_present():
            console.print(
                f"[red]Extraction finished but initdb not at "
                f"{_install_dir()/'bin'/'initdb'}.[/red] Check the URL "
                f"({_tarball_url()}) — EDB may have renamed the asset."
            )
            return

    cfg = _load_config() or {}
    cfg.setdefault("version", _PG_VERSION)
    cfg.setdefault("port", _DEFAULT_PORT)
    cfg.setdefault("password", "")
    cfg["install_dir"] = str(_install_dir())
    _save_config(cfg)

    _copy_wrappers()

    console.print(
        Panel.fit(
            f"[green]PostgreSQL {_PG_VERSION} ready.[/green]\n"
            f"  install dir: [dim]{_install_dir()}[/dim]\n"
            f"  data dir:    [dim]{_DATA}[/dim] (created on first start)\n"
            f"  config:      [dim]{_CONFIG_PATH}[/dim]\n"
            f"  wrappers:    [dim]{_BIN_DIR}/{{{', '.join(_WRAPPER_NAMES)}}}[/dim]\n\n"
            f"[bold]Next:[/bold] [dim]postgres-up[/dim] (default port 5432, trust auth).\n"
            f"[dim]postgres-up -p 5433 --pass mysecret[/dim] to set both at once.\n"
            f"[dim]postgres-up -h[/dim] for help.",
            border_style="green",
            title="Installed",
        )
    )


def _do_uninstall_keep_data() -> None:
    if _pid_running():
        console.print(
            "[yellow]Stop PostgreSQL first with `postgres-down` before "
            "uninstalling.[/yellow]"
        )
        return
    version_dir = _INSTALLS / _PG_VERSION
    if version_dir.exists():
        mutating_check(f"rm -rf {version_dir}")
        shutil.rmtree(version_dir, ignore_errors=True)
    if _RUNTIME.exists():
        mutating_check(f"rm -rf {_RUNTIME}")
        shutil.rmtree(_RUNTIME, ignore_errors=True)
    console.print(
        Panel.fit(
            f"[green]Binaries removed.[/green]\n"
            f"  kept: [dim]{_DATA}[/dim]\n"
            f"  kept: [dim]{_CONFIG_PATH}[/dim]\n"
            f"  kept: wrappers in [dim]{_BIN_DIR}[/dim]\n\n"
            "Re-run the Install option to bring the binaries back; "
            "your databases stay intact.",
            border_style="green",
            title="Uninstalled (data kept)",
        )
    )


def _do_uninstall_wipe() -> None:
    if _pid_running():
        console.print(
            "[yellow]Stop PostgreSQL first with `postgres-down` before "
            "wiping.[/yellow]"
        )
        return
    if _ROOT.exists():
        mutating_check(f"rm -rf {_ROOT}")
        shutil.rmtree(_ROOT, ignore_errors=True)
    _remove_wrappers()
    console.print(
        Panel.fit(
            f"[green]Wiped everything.[/green]\n"
            f"  removed: [dim]{_ROOT}[/dim]\n"
            f"  removed: wrappers in [dim]{_BIN_DIR}[/dim]\n\n"
            "Nothing of PostgreSQL remains on disk.",
            border_style="green",
            title="Uninstalled (wiped)",
        )
    )


def _do_status() -> None:
    state = _state()
    cfg = _load_config()
    if state == "not-installed":
        console.print("[dim]Not installed.[/dim]")
        return
    pid_file = _DATA / "postmaster.pid"
    pid = "—"
    if pid_file.exists():
        try:
            pid = pid_file.read_text().splitlines()[0].strip()
        except (OSError, IndexError):
            pid = "—"
    lines = [
        f"  state:       [bold]{state}[/bold]" + (f" (PID {pid})" if state == "running" else ""),
        f"  version:     {cfg['version']}" if cfg else "",
        f"  install dir: [dim]{_install_dir()}[/dim]",
        f"  data dir:    [dim]{_DATA}[/dim]",
        f"  port:        {cfg['port']}" if cfg else "",
        f"  password:    {'(set)' if cfg and cfg.get('password') else '(empty / trust auth)'}" if cfg else "",
    ]
    console.print("\n".join(line for line in lines if line))


def _do_start() -> None:
    wrapper = _BIN_DIR / "postgres-up"
    if not wrapper.exists():
        console.print(
            f"[red]Wrapper not found at {wrapper}.[/red] Run Install first."
        )
        return
    console.rule(f"[bold]{wrapper}[/bold]")
    mutating_run([str(wrapper)])


def _do_stop() -> None:
    wrapper = _BIN_DIR / "postgres-down"
    if not wrapper.exists():
        console.print(
            f"[red]Wrapper not found at {wrapper}.[/red] Run Install first."
        )
        return
    console.rule(f"[bold]{wrapper}[/bold]")
    mutating_run([str(wrapper)])


def manage_postgres() -> None:
    if sys.platform != "darwin":
        console.print(
            f"[red]This module is macOS-only for now.[/red] "
            "Windows support is planned (same code, different archive slug)."
        )
        return

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt Install / Status / Start / Stop / "
            "Uninstall(keep) / Uninstall(wipe). Install downloads "
            f"[dim]{_tarball_url()}[/dim] to [dim]{_install_dir()}[/dim], "
            f"writes [dim]{_CONFIG_PATH}[/dim], and copies "
            f"[dim]{', '.join(_WRAPPER_NAMES)}[/dim] into [dim]{_BIN_DIR}[/dim]."
        )
        return

    state = _state()
    choices: list[questionary.Choice] = []
    if state == "not-installed":
        choices.append(
            questionary.Choice(title=f"Install PostgreSQL {_PG_VERSION}", value="install")
        )
    else:
        choices.append(
            questionary.Choice(title=f"Status (current: {state})", value="status")
        )
        if state == "stopped":
            choices.append(
                questionary.Choice(
                    title="Start (default port + saved password)", value="start"
                )
            )
        if state == "running":
            choices.append(questionary.Choice(title="Stop", value="stop"))
        choices.append(
            questionary.Choice(
                title="Uninstall (keep data)", value="uninstall-keep"
            )
        )
        choices.append(
            questionary.Choice(
                title="Uninstall (wipe everything)", value="uninstall-wipe"
            )
        )
    choices.append(questionary.Choice(title="← Back", value="__back"))

    action = questionary.select(
        f"PostgreSQL — current state: [{state}]",
        choices=choices,
    ).ask()

    if action in (None, "__back"):
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    dispatch = {
        "install": _do_install,
        "status": _do_status,
        "start": _do_start,
        "stop": _do_stop,
        "uninstall-keep": _do_uninstall_keep_data,
        "uninstall-wipe": _do_uninstall_wipe,
    }
    dispatch[action]()


module = Module(
    key="postgres",
    title="PostgreSQL (standalone binaries)",
    description=(
        f"Standalone PostgreSQL {_PG_VERSION} — EDB binaries, no brew/sudo/Docker. "
        "Installs wrappers (postgres-up / -down / -status / -cli) in ~/.local/bin/."
    ),
    run=manage_postgres,
)

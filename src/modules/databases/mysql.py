from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tarfile
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
from style import QUESTIONARY_STYLE

_MYSQL_VERSION = "8.4.3"
_DEFAULT_PORT = 3306
_PORT_PROBE_LIMIT = 20

_ROOT = Path.home() / ".local" / "share" / "mac-fresh-setup" / "mysql"
_INSTALLS = _ROOT / "installs"
_DATA = _ROOT / "data"
_RUNTIME = _ROOT / "runtime"
_CONFIG_PATH = _ROOT / "config.json"
_BIN_DIR = Path.home() / ".local" / "bin"
_WRAPPER_NAMES = ("mysql-up", "mysql-down", "mysql-status", "mysql-cli", "mysql-debug")
_REPO_WRAPPER_DIR = Path(__file__).resolve().parents[3] / "config" / "mysql" / "wrappers"


def _platform_suffix() -> str:
    if sys.platform == "darwin":
        arch = "arm64" if platform.machine() == "arm64" else "x86_64"
        return f"macos14-{arch}"
    if sys.platform == "win32":
        return "winx64"
    return ""


def _archive_ext() -> str:
    return "zip" if sys.platform == "win32" else "tar.gz"


def _archive_basename() -> str:
    return f"mysql-{_MYSQL_VERSION}-{_platform_suffix()}"


def _tarball_url() -> str:
    major = ".".join(_MYSQL_VERSION.split(".")[:2])
    return (
        f"https://dev.mysql.com/get/Downloads/MySQL-{major}/"
        f"{_archive_basename()}.{_archive_ext()}"
    )


def _install_dir() -> Path:
    return _INSTALLS / _MYSQL_VERSION / _archive_basename()


def _mysqld_exe() -> str:
    return "mysqld.exe" if sys.platform == "win32" else "mysqld"


def _binaries_present() -> bool:
    return (_install_dir() / "bin" / _mysqld_exe()).exists()


def _load_config() -> dict | None:
    if not _CONFIG_PATH.exists():
        return None
    return json.loads(_CONFIG_PATH.read_text())


def _save_config(cfg: dict) -> None:
    _ROOT.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
    _CONFIG_PATH.chmod(0o600)


def _pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0 and str(pid) in result.stdout
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _pid_running() -> bool:
    pid_file = _RUNTIME / "mysql.pid"
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        return False
    return _pid_alive(pid)


def _state() -> Literal["not-installed", "running", "stopped"]:
    if not _binaries_present():
        return "not-installed"
    return "running" if _pid_running() else "stopped"


def _rmtree_robust(path: Path) -> list[str]:
    """Remove a tree, retry once after 2s on permission errors, and report leftovers.

    On Windows, AV scanners (and pending file handles) can briefly hold
    files locked. We retry once with a short pause, then chmod-777 each
    failing entry and try a final pass. Anything still left is returned
    as a list of "path: reason" strings so the caller can surface it to
    the user instead of silently lying about a successful wipe.
    """
    import time as _time

    failures: list[str] = []

    def _onerror(func, p, exc_info):
        try:
            os.chmod(p, 0o777)
            func(p)
        except Exception as nested:
            failures.append(f"{p}: {nested}")

    for attempt in range(2):
        failures.clear()
        try:
            shutil.rmtree(path, onerror=_onerror)
            if not path.exists() and not failures:
                return []
        except FileNotFoundError:
            return []
        except Exception as exc:
            failures.append(f"{path}: {exc}")
        if attempt == 0:
            _time.sleep(2)

    return failures


def _is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _find_free_port(start: int = _DEFAULT_PORT, limit: int = _PORT_PROBE_LIMIT) -> int:
    for candidate in range(start, start + limit):
        if _is_port_free(candidate):
            return candidate
    return start


def _wrapper_invocation(name: str) -> list[str]:
    """Argv to execute a wrapper from `_BIN_DIR`."""
    if sys.platform == "win32":
        return [str(_BIN_DIR / f"{name}.cmd")]
    return [str(_BIN_DIR / name)]


def _wrapper_exists(name: str) -> bool:
    if sys.platform == "win32":
        return (_BIN_DIR / f"{name}.cmd").exists() and (_BIN_DIR / f"{name}.py").exists()
    return (_BIN_DIR / name).exists()


def _copy_wrappers() -> None:
    mutating_check(f"copy MySQL wrappers to {_BIN_DIR}")
    _BIN_DIR.mkdir(parents=True, exist_ok=True)
    for name in _WRAPPER_NAMES:
        src = _REPO_WRAPPER_DIR / name
        if sys.platform == "win32":
            py_dst = _BIN_DIR / f"{name}.py"
            cmd_dst = _BIN_DIR / f"{name}.cmd"
            shutil.copyfile(src, py_dst)
            cmd_dst.write_text(
                "@echo off\r\n"
                f'uv run --no-project --quiet "%~dp0{name}.py" %*\r\n'
            )
        else:
            dst = _BIN_DIR / name
            shutil.copyfile(src, dst)
            dst.chmod(0o755)


def _remove_wrappers() -> None:
    mutating_check(f"remove MySQL wrappers from {_BIN_DIR}")
    for name in _WRAPPER_NAMES:
        if sys.platform == "win32":
            (_BIN_DIR / f"{name}.py").unlink(missing_ok=True)
            (_BIN_DIR / f"{name}.cmd").unlink(missing_ok=True)
        else:
            (_BIN_DIR / name).unlink(missing_ok=True)


def _download_and_extract() -> None:
    url = _tarball_url()
    console.print(f"[dim]Downloading {url}[/dim]")
    with tempfile.NamedTemporaryFile(
        suffix=f".{_archive_ext()}", delete=False
    ) as tmp:
        archive = Path(tmp.name)
    try:
        rc = mutating_run(
            ["curl", "-fL", "--progress-bar", "-o", str(archive), url]
        ).returncode
        if rc != 0:
            raise RuntimeError(f"curl exited with {rc}")
        target = _INSTALLS / _MYSQL_VERSION
        target.mkdir(parents=True, exist_ok=True)
        console.print(f"[dim]Extracting to {target}...[/dim]")
        if _archive_ext() == "zip":
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(target)
        else:
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(target)
    finally:
        archive.unlink(missing_ok=True)


def _do_install() -> None:
    if _binaries_present():
        console.print(
            f"[yellow]Binaries already at {_install_dir()} — skipping download.[/yellow]"
        )
    else:
        _download_and_extract()
        if not _binaries_present():
            console.print(
                f"[red]Extraction finished but mysqld not at {_install_dir()/'bin'/'mysqld'}.[/red]"
            )
            return

    cfg = _load_config() or {}
    cfg.setdefault("version", _MYSQL_VERSION)
    cfg.setdefault("password", "")
    if "port" not in cfg or not _is_port_free(cfg["port"]):
        previous = cfg.get("port")
        chosen = _find_free_port()
        cfg["port"] = chosen
        if previous is None and chosen != _DEFAULT_PORT:
            console.print(
                f"[yellow]Port {_DEFAULT_PORT} is already bound on this machine[/yellow] "
                f"(likely an existing MySQL service). Auto-selected the next free port: "
                f"[bold]{chosen}[/bold]. Saved to config — every wrapper uses it."
            )
        elif previous is not None and previous != chosen:
            console.print(
                f"[yellow]Previously-saved port {previous} is now busy[/yellow] — "
                f"another process took it. Re-autodetected: [bold]{chosen}[/bold]. "
                "Config updated."
            )
    cfg["install_dir"] = str(_install_dir())
    _save_config(cfg)

    _copy_wrappers()

    port = cfg["port"]
    console.print(
        Panel.fit(
            f"[green]MySQL {_MYSQL_VERSION} ready.[/green]\n"
            f"  install dir: [dim]{_install_dir()}[/dim]\n"
            f"  data dir:    [dim]{_DATA}[/dim] (created on first start)\n"
            f"  config:      [dim]{_CONFIG_PATH}[/dim]\n"
            f"  wrappers:    [dim]{_BIN_DIR}/{{{', '.join(_WRAPPER_NAMES)}}}[/dim]\n"
            f"  port:        [bold]{port}[/bold]\n\n"
            f"[bold]Next:[/bold] [dim]mysql-up[/dim] (port {port}, no password).\n"
            f"[dim]mysql-up --pass mysecret[/dim] to set a root password.\n"
            "[dim]mysql-up -h[/dim] for help.",
            border_style="green",
            title="Installed",
        )
    )


def _do_uninstall_keep_data() -> None:
    if _pid_running():
        console.print("[yellow]Stop MySQL first with `mysql-down` before uninstalling.[/yellow]")
        return
    version_dir = _INSTALLS / _MYSQL_VERSION
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
        console.print("[yellow]Stop MySQL first with `mysql-down` before wiping.[/yellow]")
        return
    confirmed = questionary.confirm(
        f"This will PERMANENTLY delete {_ROOT} (binaries, data, config) "
        f"and the four wrappers in {_BIN_DIR}. Continue?",
        default=False,
        style=QUESTIONARY_STYLE,
    ).ask()
    if not confirmed:
        console.print("[yellow]Aborted — nothing removed.[/yellow]")
        return
    failures: list[str] = []
    if _ROOT.exists():
        mutating_check(f"rm -rf {_ROOT}")
        failures = _rmtree_robust(_ROOT)
    _remove_wrappers()
    if failures:
        console.print(
            Panel.fit(
                f"[yellow]Wipe completed with leftovers.[/yellow]\n"
                f"  removed: wrappers in [dim]{_BIN_DIR}[/dim]\n\n"
                f"[bold]Could not remove:[/bold]\n"
                + "\n".join(f"  [dim]{f}[/dim]" for f in failures)
                + "\n\nLikely an antivirus / file lock. Close anything that "
                "might be scanning the install dir, then re-run Uninstall(wipe).",
                border_style="yellow",
                title="Uninstalled (partial)",
            )
        )
        return
    console.print(
        Panel.fit(
            f"[green]Wiped everything.[/green]\n"
            f"  removed: [dim]{_ROOT}[/dim]\n"
            f"  removed: wrappers in [dim]{_BIN_DIR}[/dim]\n\n"
            "Nothing of MySQL remains on disk.",
            border_style="green",
            title="Uninstalled (wiped)",
        )
    )


def _do_refresh_wrappers() -> None:
    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would re-copy "
            f"[dim]{', '.join(_WRAPPER_NAMES)}[/dim] into [dim]{_BIN_DIR}[/dim]."
        )
        return
    _copy_wrappers()
    console.print(
        f"[green]Refreshed wrappers in {_BIN_DIR}.[/green] "
        f"({', '.join(_WRAPPER_NAMES)})"
    )


def _do_start() -> None:
    if not _wrapper_exists("mysql-up"):
        console.print(
            f"[red]mysql-up wrapper not found in {_BIN_DIR}.[/red] Run Install first."
        )
        return
    cmd = _wrapper_invocation("mysql-up")
    console.rule(f"[bold]{' '.join(cmd)}[/bold]")
    mutating_run(cmd)


def _do_stop() -> None:
    if not _wrapper_exists("mysql-down"):
        console.print(
            f"[red]mysql-down wrapper not found in {_BIN_DIR}.[/red] Run Install first."
        )
        return
    cmd = _wrapper_invocation("mysql-down")
    console.rule(f"[bold]{' '.join(cmd)}[/bold]")
    mutating_run(cmd)


def _do_status() -> None:
    state = _state()
    cfg = _load_config()
    if state == "not-installed":
        console.print("[dim]Not installed.[/dim]")
        return
    pid_file = _RUNTIME / "mysql.pid"
    pid = pid_file.read_text().strip() if pid_file.exists() else "—"
    port = cfg["port"] if cfg else None
    port_busy = (port is not None) and (not _is_port_free(port))
    if state == "running":
        port_line = f"  listening:   [bold green]127.0.0.1:{port}[/bold green]"
    elif port is not None:
        marker = " [yellow](in use by another process)[/yellow]" if port_busy else " [dim](free)[/dim]"
        port_line = f"  port:        [bold]{port}[/bold]{marker}"
    else:
        port_line = ""
    lines = [
        f"  state:       [bold]{state}[/bold]" + (f" (PID {pid})" if state == "running" else ""),
        f"  version:     {cfg['version']}" if cfg else "",
        f"  install dir: [dim]{_install_dir()}[/dim]",
        f"  data dir:    [dim]{_DATA}[/dim]",
        port_line,
        f"  password:    {'(set)' if cfg and cfg.get('password') else '(empty)'}" if cfg else "",
        f"  socket:      [dim]{_RUNTIME / 'mysql.sock'}[/dim]" if state == "running" and sys.platform != "win32" else "",
        f"  log:         [dim]{_RUNTIME / 'mysql.log'}[/dim]" if state == "running" else "",
    ]
    console.print("\n".join(line for line in lines if line))


def manage_mysql() -> None:
    if sys.platform not in ("darwin", "win32"):
        console.print(
            f"[red]This module supports macOS and Windows only.[/red] "
            "Linux support is not implemented yet."
        )
        return
    if sys.platform == "win32" and platform.machine().lower() in ("arm64", "aarch64"):
        console.print(
            "[yellow]Windows ARM64 detected.[/yellow] MySQL only publishes "
            "[bold]winx64[/bold] binaries — they will run via Windows' x64 "
            "emulation (Prism). Expect some startup overhead; functionally "
            "correct."
        )

    if runtime.dry_run:
        console.print(
            f"[cyan]DRY RUN[/cyan] would prompt Install / Status / Start / Stop / "
            "Uninstall(keep) / Uninstall(wipe). Install downloads "
            f"[dim]{_tarball_url()}[/dim] to [dim]{_install_dir()}[/dim], "
            f"writes [dim]{_CONFIG_PATH}[/dim], and copies "
            f"[dim]{', '.join(_WRAPPER_NAMES)}[/dim] into [dim]{_BIN_DIR}[/dim]. "
            "Daemon control is delegated to the wrappers (mysql-up / mysql-down)."
        )
        return

    state = _state()
    choices: list[questionary.Choice] = []
    if state == "not-installed":
        choices.append(
            questionary.Choice(title=f"Install MySQL {_MYSQL_VERSION}", value="install")
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
                title="Refresh wrappers (re-copy from repo, no download)",
                value="refresh-wrappers",
            )
        )
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
        f"MySQL — current state: [{state}]",
        choices=choices,
        style=QUESTIONARY_STYLE,
    ).ask()

    if action in (None, "__back"):
        console.print("[yellow]Returning to menu.[/yellow]")
        return

    dispatch = {
        "install": _do_install,
        "status": _do_status,
        "start": _do_start,
        "stop": _do_stop,
        "refresh-wrappers": _do_refresh_wrappers,
        "uninstall-keep": _do_uninstall_keep_data,
        "uninstall-wipe": _do_uninstall_wipe,
    }
    dispatch[action]()


module = Module(
    key="mysql",
    title="MySQL (standalone tarball)",
    description=(
        f"Standalone MySQL {_MYSQL_VERSION} — official tarball, no brew/sudo/Docker. "
        "Installs wrappers (mysql-up / -down / -status / -cli) in ~/.local/bin/."
    ),
    run=manage_mysql,
)

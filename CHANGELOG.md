# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--dry-run` flag: each module checks state, prints what it **would** do, then returns without touching the system. Useful to verify idempotency and inspect generated commands.
- `src/runtime.py` — module-level `Runtime` dataclass carrying global flags. `app.py` sets `runtime.dry_run` from `argparse` before the menu starts; modules read it on entry.
- Module: **XCode Command Line Tools** (`src/modules/xcode_cli.py`) under the System category. On install, triggers `xcode-select --install` (GUI dialog), shows an instruction panel, blocks on `press_any_key_to_continue`, then verifies. Required prerequisite for Homebrew.
- `src/safe.py` — `MAC_FRESH_SETUP_SAFE=1` hard guard. `mutating_run(cmd)` wraps subprocess calls that change state; `mutating_check(description)` precedes non-subprocess mutations (mkdir, file writes, chmod-on-new-files). When SAFE is set, either helper prints the blocked command and `SystemExit(1)`. Independent from `--dry-run` — dry-run is for inspection, SAFE is for defense in depth during local testing.
- `scripts/smoke.py` — single-command smoke test. Patches `subprocess.run` with a recorder, exports `MAC_FRESH_SETUP_SAFE=1`, sets `runtime.dry_run = True`, then runs every module under every category. Reports recorded calls per module and fails if any module attempts a mutating action. Run it with `uv run --with questionary --with rich python scripts/smoke.py` — this is the new step-1 of the ship sequence.

### Changed
- **XCode CLI detection** — replaced `pkgutil --pkg-info=com.apple.pkg.CLTools_Executables` with `xcode-select -p` + check that `<dev>/usr/bin/clang` exists. The pkgutil package id varies across macOS versions (and was returning false-negative on macOS Tahoe), the clang-existence check is uniformly reliable for both CLT-only and full-Xcode installs. On failure, the module now prints a diagnostic block (rc, stdout, stderr, dev-dir existence, clang existence) before asking the user to re-run.
- **XCode CLI wait flow** — replaced "press any key when install finishes" with active polling. After triggering `xcode-select --install`, the module displays a `rich.Progress` spinner and polls `xcode-select -p` + clang existence every 5 seconds (15-minute timeout). Removes a footgun where users hit a key before completing the GUI dialog, leaving CLT half-installed.
- Migrated `sudoers`, `ssh_key`, `xcode_cli` to use `safe.mutating_run` / `safe.mutating_check` for state-changing calls.

### How to use

```sh
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py" --dry-run
```

(Earlier docs suggested `-- --dry-run`; that doesn't work on uv `0.11.x` — uv passes the `--` through to the script and argparse rejects it.)

## [0.1.3] — 2026-05-16

> Progress checkpoint — not tagged.

### Changed
- **Project layout** — code moved from a single `setup.py` (217 lines) into `src/`. `setup.py` is now a ~50-line bootstrap that downloads the repository tarball from `codeload.github.com`, extracts it into a temp directory (cleaned up on exit), inserts `src/` at `sys.path[0]`, and runs `app.run`.
- Structure: `src/{app,console,models,categories}.py` + `src/modules/{sudoers,ssh_key}.py`. No `mac_fresh_setup/` namespace package — a single-app project doesn't need one, imports are flat (`from console import console`).
- Removed empty skeleton dirs at the repo root (`modules/`, `config/`, `tests/`) that were created at project init but never populated.
- `MAC_FRESH_SETUP_REF` env var overrides the ref to fetch (default `main`); use this to pin to a tag.

### Why
- The single-file constraint of `uv run <url>` was forcing all logic into one file. The bootstrap pattern keeps the entry point small (deps still declared in PEP 723) while the rest of the code lives in normal, navigable, testable files. Flat `src/` layout (no package namespace) keeps imports short for a single-app project.

## [0.1.2] — 2026-05-16

> Progress checkpoint — not tagged.

### Changed
- Menu redesigned as a hub: main menu lists **categories**, picking one opens a submenu of modules. Each module runs in isolation; after it finishes you return to the submenu. From any submenu, `← Back` returns to the main menu; main menu has `Exit`.
- Modules are now grouped under a `Category`. First category: **System** (sudoers + ssh-key). Future categories planned: Package manager (Homebrew), Shell (oh-my-zsh/spaceship/zshrc), Languages (asdf), Editor (VSCode).

### Why
- Multi-select (`questionary.checkbox`) ran every selected module in a single pass with no chance to skip mid-way, and the script exited to the shell at the end. The hub pattern lets the user pick one module, watch it complete, and decide what to do next — and keeps the menu manageable as more modules land.

## [0.1.1] — 2026-05-16

> Progress checkpoint — not tagged. Tags land only on milestone releases.

### Changed
- Module menu shows only the short title; the per-module description no longer renders inline (kept on the `Module` dataclass for future use).
- Shortened module titles: `Grant Root Access (sudoers NOPASSWD)` → `Grant Root Access`; `SSH Key (RSA 4096)` → `SSH Key`.

### Documentation
- README: added `--refresh` and cache-buster query usage to bypass `uv` + GitHub raw CDN caching during development.

## [0.1.0] — 2026-05-16

### Added
- `setup.py` — PEP 723 single-file CLI runnable via `uv run <url>`.
- Interactive `questionary` checkbox menu to pick which modules to run.
- Module: **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD`, validated via `visudo -cf`, installed with `install -m 0440`.
- Module: **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions to `0400`, prints the public key in a `rich` panel for copy-paste into GitHub.
- Preflight check: macOS only, requires `sudo` and `ssh-keygen` on `PATH`.
- `README.md` with `uv` install prerequisite and one-line run command.
- `docs/fresh-install.md` — reference gist content used as source of truth.

[Unreleased]: https://github.com/lipex360x/mac-fresh-setup/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/lipex360x/mac-fresh-setup/releases/tag/v0.1.0

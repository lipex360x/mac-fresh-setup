# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Claude Code on native Windows.** The previous module piped `claude.ai/install.sh` into `bash` everywhere — on Windows that script detects the OS and tries to delegate to WSL, failing with `Windows Subsystem for Linux has no installed distributions` on fresh boxes. `claude_code.py` now branches on `sys.platform`: macOS/Linux keep `curl -fsSL https://claude.ai/install.sh | bash`; Windows runs the official PowerShell installer via `powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"`. No Node, no npm, no admin/UAC — native binary lands at `%USERPROFILE%\.local\bin\claude.exe`. The `cc` alias target also switches: `~/.zshrc` on macOS/Linux, `~/.bashrc` on Windows (Git Bash).

### Added
- **Chocolatey install module** (`src/modules/package_manager/chocolatey_install.py`, `platforms={"win32"}`). Windows analogue to Homebrew — sits in the Package manager category, idempotent via `shutil.which("choco")` + the canonical path `C:\ProgramData\chocolatey\bin\choco.exe`. Install path: launches an **elevated PowerShell** via `Start-Process -Verb RunAs -Wait`, runs the official `https://community.chocolatey.org/install.ps1` script under a `Bypass` execution policy, and waits for the UAC-elevated window to exit. After install, instructs the user to reopen Git Bash so `choco` lands on PATH for subsequent modules. Wired into `categories.py` between `homebrew_install` and `homebrew_packages`; on macOS/Linux the platform filter hides it.

### Changed
- **Banner is now platform-agnostic.** Renamed `mac-fresh-setup` → **OS Fresh Setup** in the welcome panel and the argparse prog/description. Subtitle now reads "Interactive bootstrap for a fresh install (macOS / Linux / Windows)" so the Windows menu no longer claims to be for macOS only.

### Added
- **`cc` alias for Claude Code.** After installing Claude Code, the module now appends `alias cc='claude --dangerously-skip-permissions'` to `~/.zshrc` (idempotent — checks for the exact line before writing). The same alias is baked into the bundled `config/zsh/.zshrc`, so the Styling → Zsh stack module also lands it on a fresh install regardless of which module runs first. Re-running Claude Code on a host that already has `claude` on PATH still injects the alias if missing.

### Changed
- **PHP delivery: mise → Laravel Herd.** Dropped `Runtime("PHP 8.3", "php@8.3", ...)` from `src/modules/package_manager/mise_runtimes.py`. PHP was the only mise runtime that compiled from source (via `asdf-php`), which required 12 brew formulae as build dependencies (`autoconf`, `bison`, `re2c`, `gd`, `libsodium`, `pkg-config`, `libpq`, `libzip`, `libxml2`, `openssl@3`, `libiconv`, `libjpeg`, `curl`) and 5–10 min compile time. Replaced with `Package("herd", "cask", ...)` in `homebrew_packages.py` — Laravel Herd is a pre-compiled standalone app bundling PHP (multiple versions side-by-side), composer, nginx, and dnsmasq. Zero build deps, instant install. README `Running PHP` section rewritten around the Herd flow; `cleanup_paths=("Library/Application Support/Herd", ".config/herd-lite")` wired so uninstall wipes state cleanly.

### Fixed
- **Mise picker** — `rt.spec` was wrapped in literal `[dim]...[/dim]` rich markup tags, which questionary renders as plain text (it doesn't parse rich markup). The spec is now shown as plain `(node@lts)` without leaking tags.

## [0.2.0] — 2026-05-16

Major release. New categories (Package manager, Styling, Databases), full standalone-binary DB stack, install/uninstall flow, hard safety net, cyan UI face-lift.

### Added
- **Package manager** category and module **Homebrew** (`src/modules/homebrew_install.py`). Fetches `Homebrew/install/HEAD/install.sh` via `curl`, pipes it into `/bin/bash` with `NONINTERACTIVE=1`, then appends `eval "$(<prefix>/bin/brew shellenv)"` to `~/.zprofile` (idempotent — only if line not present). Detects brew via `shutil.which` + the two canonical prefixes (`/opt/homebrew` Apple Silicon, `/usr/local` Intel). Dry-run prints the planned download + zprofile edit.
- **In-process brew activation** — after installing/locating brew, the module runs `bash -c 'eval "$(brew shellenv)" && env'` and copies `PATH`, `HOMEBREW_PREFIX`, `HOMEBREW_CELLAR`, `HOMEBREW_REPOSITORY`, `MANPATH`, `INFOPATH` into `os.environ`. Subsequent modules in the same session (future formulae/casks) can call `brew` directly without reopening the user's terminal. The user's parent shell still needs `source ~/.zprofile` or a new terminal — child processes can't mutate the parent shell, that's a Unix limitation.
- Module: **Homebrew packages** (`src/modules/package_manager/homebrew_packages.py`). Single curated list mixing formulae and casks; cask items are tagged `[cask]` in the title. Uses one `questionary.checkbox` with defaults unchecked, descriptions on hover, already-installed items greyed out (queries `brew list --formula --versions` + `brew list --cask --versions` once). Dispatches to `brew install <name>` or `brew install --cask <name>` based on the package's `kind`. Includes a `← Back` choice that returns without installing.
- Initial package list: formulae `mise`, `gh`, `bun`; casks `iterm2`, `visual-studio-code`, `font-fira-code`, `intellij-idea-ce`, `docker-desktop`, `bruno`, `the-unarchiver`, `mockoon`, `beekeeper-studio`, `bitwarden`, `aldente`, `betterdisplay`, `raycast`, `orka-desktop`. Casks/formulae from the reference gist.
- Reordered the package list with `brave-browser` and `the-unarchiver` at the top, removed `bun` (will land via mise) and `raycast` (deferred).

### Removed
- `src/modules/package_manager/homebrew_formulae.py` and `homebrew_casks.py` — merged into the single `homebrew_packages` module above.

### Changed (UI face-lift — cyan questionary theme)
- New `src/style.py` exposing `QUESTIONARY_STYLE` with a cyan (`#00d7ff`) accent palette for `qmark`, `pointer`, `highlighted`, `selected`, `answer`; greys for `instruction` and `disabled`. Pattern adopted from the sibling `cct-netbeans-setup` project.
- Plumbed `style=QUESTIONARY_STYLE` through every interactive call in the codebase (14 sites across `app.py`, the system/package_manager/databases modules). Menus, prompts, confirmations and the press-any-key gate now render consistently cyan instead of questionary's default bright-green/blue.

### Fixed (PostgreSQL — symlinks)
- Even with Rosetta installed, the very first `initdb` still failed: `dyld: Library not loaded: ... libicudata.68.dylib (slice is not valid mach-o file)`. Root cause: Python's `zipfile.extractall` materialises **symlinks as text files** containing the target path, instead of recreating them as actual symlinks. EDB packages `libicudata.dylib → libicudata.68.dylib` (and several similar) — the broken "symlink" gets loaded as a malformed dylib.
- Fix: `_extract_zip_preserving_perms` now checks `stat.S_ISLNK(info.external_attr >> 16)` on each entry. Symlink entries are recreated via `Path.symlink_to(link_target)` instead of being written to disk as text.

### Fixed (PostgreSQL on Apple Silicon)
- EDB only ships **x86_64 macOS** PostgreSQL binaries — no arm64 native build (confirmed across all 17.x and 18.x). Result: on Apple Silicon Macs the freshly-extracted `initdb` fails with `dyld: Library not loaded: ... (slice is not valid mach-o file)`.
- Fix: detect Apple Silicon (`platform.machine() == "arm64"`) and ensure Rosetta 2 is present before downloading. Detection via `arch -x86_64 /usr/bin/true` exit code. If missing, runs `sudo softwareupdate --install-rosetta --agree-to-license` (one-time, ~150 MB from Apple).
- Bumped default version to **17.10** (latest current patch as of May 2026; previous default `17.4` was already stale).
- ZIP extraction now preserves Unix mode bits via a small helper — Python's `ZipFile.extractall` drops the executable bit so EDB's `bin/initdb` would extract as `0644` and fail on first run.

### Added (PostgreSQL)
- Second module under Databases: **PostgreSQL (standalone binaries)** (`src/modules/databases/postgres.py`). Mirrors the MySQL design end-to-end — same install/uninstall flow, same wrapper pattern, same config.json shape.
- Install path: downloads `https://get.enterprisedb.com/postgresql/postgresql-17.4-1-osx-binaries.zip` (EDB binary distribution, no source compile), extracts to `~/.local/share/mac-fresh-setup/postgres/installs/17.4/pgsql/`. PostgreSQL doesn't have an official tarball on `postgresql.org` for macOS so EDB is the de-facto portable distribution; same publisher provides `windows-x64-binaries.zip` for the future Windows variant.
- Wrappers in `~/.local/bin/`: `postgres-up [-p PORT] [--pass PASS] [-h]`, `postgres-down [-h]`, `postgres-status [-h]`, `postgres-cli [args] [-h]`. Same flag semantics as the MySQL wrappers. First run initialises the data dir via `initdb -U postgres`; with `--pass` it uses `initdb --pwfile` + `md5` auth, otherwise `trust` auth (localhost-only by default).
- Subsequent password changes flow through `ALTER USER postgres PASSWORD '...'` via `psql` (uses `PGPASSWORD` from config to authenticate).
- Stop is graceful via `pg_ctl -m fast stop`. Status reads `postmaster.pid` (first line is the PID) for the running check.
- Action picker: Install / Status / Start / Stop / Uninstall (keep data) / Uninstall (wipe). Start/Stop delegate to the wrappers — same happy-path-in-menu / advanced-in-CLI split as MySQL.

### Added (Databases category)
- New category **Databases** with the first module: **MySQL (standalone tarball)** (`src/modules/databases/mysql.py`).
- Install path: downloads the official tarball from `dev.mysql.com/get/Downloads/MySQL-8.4/mysql-8.4.3-<platform>.tar.gz` (default version `8.4.3`, current LTS), extracts into `~/.local/share/mac-fresh-setup/mysql/installs/8.4.3/`. No brew, no Mise, no sudo, no Docker — fully user-level.
- Persistent config at `~/.local/share/mac-fresh-setup/mysql/config.json` (mode `0600`): `{ "version", "install_dir", "port", "password" }`.
- Action picker: Install / Status / **Start** (when stopped) / **Stop** (when running) / Uninstall (keep data) / Uninstall (wipe everything) / ← Back. Start/Stop delegate to the wrappers with no flags — happy path for "default port + saved password". For port overrides or password rotation, run the wrappers directly from the terminal (`mysql-up -p 3307 --pass abc`).
- Daemon control is delegated to **wrappers** copied to `~/.local/bin/`:
  - `mysql-up [-p PORT] [--pass PASS] [-h]` — initializes data dir on first run, starts `mysqld_safe`, optionally sets/changes the root password (saved to config), updates port (saved to config).
  - `mysql-down [-h]` — graceful shutdown via `mysqladmin shutdown` (uses saved password if any), SIGTERM fallback.
  - `mysql-status [-h]` — prints install/data dirs, port, password presence, running PID + socket + log when up.
  - `mysql-cli [args] [-h]` — execs the `mysql` client connected via the local Unix socket using saved credentials; trailing args forwarded.
- Wrapper templates live in `config/mysql/wrappers/` and are copied into place during install (and removed on the "wipe" uninstall).
- **Uninstall (keep data)** removes only the binaries dir (`installs/<version>/`) and the runtime dir — keeps the data dir, config, wrappers. Reinstall same version = come back where you left off, databases intact.
- **Uninstall (wipe everything)** removes the whole `~/.local/share/mac-fresh-setup/mysql/` tree and all four wrappers from `~/.local/bin/`.
- Cross-platform-ready: the module branches on `sys.platform` to pick `.tar.gz` vs `.zip` archive and to switch the platform suffix (`macos14-arm64` / `macos14-x86_64` today; `winx64` once Windows lands). The wrapper scripts are pure Python and need no changes for Windows.

### Added (Uninstall cleanup paths)
- `Package` dataclass now accepts an optional `cleanup_paths` tuple — paths under `$HOME` to `rm -rf` after a successful `brew uninstall`. `visual-studio-code` ships with: `Library/Application Support/Code`, `Library/Application Support/Code - Insiders`, `.vscode`, `.vscode-insiders`. The uninstall flow first runs `brew uninstall --cask <name>`, then iterates the cleanup paths (only the ones that exist on disk) through `safe.mutating_check` + `shutil.rmtree`. CLAUDE.md table updated to document the new field.

### Added (Install / Uninstall)
- `Homebrew packages` and `Mise runtimes` now prompt **Install / Uninstall / Back** before showing the checkbox. Each picker only lists items that are actionable: install mode shows only **not-installed** items, uninstall mode shows only **installed** items. Empty lists short-circuit with a friendly "nothing to do" message. Selected items run `brew install` / `brew uninstall` (with `--cask` when needed) or `mise use -g <spec>` / `mise uninstall <spec>`. Same module, two intents — no duplicate menu entry.

### Added (Claude Code)
- Module **Claude Code** (`src/modules/package_manager/claude_code.py`) at the top of the Package manager category. Idempotency via `shutil.which("claude")`. Install path: `curl -fsSL https://claude.ai/install.sh | bash`. No brew, no Node, no PEP — runs on a truly fresh macOS. Lands before Homebrew in the menu so you can have Claude Code available immediately on a new machine.

### Added (mise runtimes)
- Module **Mise runtimes** (`src/modules/package_manager/mise_runtimes.py`) under Package manager. Checkbox over a `Runtime(title, spec, description)` list: Node.js LTS (`node@lts`), Bun latest (`bun@latest`), Java LTS (`java@temurin-25` — Java 25 LTS released Sep 2025), PHP 8.3 (`php@8.3`). Idempotency via `mise current <tool>`; already-set runtimes are greyed out. Each selected entry runs `mise use -g <spec>` with live output.

### Added (VSCode extensions list expansion)
- Extended the curated VSCode extensions list with: `github.copilot`, `github.copilot-chat`, `ms-azuretools.vscode-docker`, `ms-python.python`, `redhat.java`, `oven.bun-vscode`, `editorconfig.editorconfig`, `usernamehw.errorlens`.

### Documentation
- `CLAUDE.md`: structure section refreshed to match the current layout (categories include `editor/` and the `config/` bundle dir). Added a "Curated lists — how to add an item" section documenting the same pattern across the three picker modules (`homebrew_packages`, `mise_runtimes`, `vscode_extensions`).
- New category **Styling** with module **iTerm2 preferences** (`src/modules/styling/iterm2_prefs.py`). Fetches the plist from `config/iterm2/com.googlecode.iterm2.plist` checked into this repo (override with `ITERM2_PREFS_URL` env var); backs up any existing `~/Library/Preferences/com.googlecode.iterm2.plist`, writes the new file, runs `killall cfprefsd` to invalidate macOS's preference cache. On any write failure, falls back to `~/Downloads/com.googlecode.iterm2.plist` and prints manual import instructions (cp + killall cfprefsd, or iTerm2's "Load settings from custom folder or URL"). The questionary prompt was removed — the prefs file changes rarely; users override via the env var when needed.
- Added `config/iterm2/com.googlecode.iterm2.plist` — XML-form plist exported from the maintainer's Mac (`plutil -convert xml1`). Versioned with the project so the Styling module is self-contained.

### Changed (layout)
- `src/modules/` now nests one subdirectory per category: `system/`, `package_manager/`, `styling/`, `editor/`. Internal module imports (`from console import console`, etc.) unchanged — `src/` is the sys.path root, the new subdirs are just import namespaces. `src/categories.py` imports each module from its category package.

### Added (Styling — zsh stack)
- Module **Zsh stack** (`src/modules/styling/zsh_stack.py`) — combo that runs Oh-my-zsh → Spaceship → Custom .zshrc in sequence with section dividers. Defaults the "always install all three" flow to a single click; individual modules stay available for re-running just one piece.
- Module **Oh-my-zsh** (`src/modules/styling/oh_my_zsh.py`) — fetches the official `install.sh` and pipes into `sh` with `RUNZSH=no CHSH=no KEEP_ZSHRC=yes` so the install doesn't open a new shell, doesn't switch the user's default shell, and doesn't overwrite an existing `~/.zshrc`. Idempotency via `~/.oh-my-zsh/oh-my-zsh.sh` presence check.
- Module **Spaceship theme** (`src/modules/styling/spaceship.py`) — `git clone --depth 1 denysdovhan/spaceship-prompt` into `~/.oh-my-zsh/custom/themes/spaceship-prompt`, then symlinks `spaceship.zsh-theme` into the OMZ themes dir so `ZSH_THEME="spaceship"` resolves. Idempotency check on both the clone and the symlink.
- Module **Custom .zshrc** (`src/modules/styling/zshrc.py`) — same pattern as iTerm2 prefs: defaults to the in-repo `config/zsh/.zshrc`, overrides via `ZSHRC_URL`. Backs up the existing `~/.zshrc` before writing.
- Added `config/zsh/.zshrc` — bundled config replicating the maintainer's styling-only setup: OMZ defaults, Spaceship prompt with custom order and colors, terminal-title hook, zinit auto-bootstrap with three plugins (`fast-syntax-highlighting`, `zsh-autosuggestions`, `zsh-completions`), and conditional `mise activate zsh`. **No** aliases or `~/.zsh_script/*` sourcing — keeping the bundle minimal until the Languages/aliases work lands.
- Added `font-fira-code` to the curated Homebrew casks list — needed by iTerm2 (which expects `FiraCode-Regular 12` per the bundled plist) and renders Spaceship's powerline glyphs properly.

### Changed (Styling menu)
- Removed the standalone **Oh-my-zsh**, **Spaceship theme**, and **Custom .zshrc** entries from the Styling menu. The three are always run together via `Zsh stack`, so listing them individually was noise. The source files stay in `src/modules/styling/` because `zsh_stack` still imports them internally — they just don't show up as menu options anymore. Matches the VSCode pattern.

### Replaced (VSCode → Styling stack)
- Removed the standalone **Editor** category and its two modules (`vscode_extensions.py` + `vscode_settings.py`).
- New module **VSCode stack** (`src/modules/styling/vscode_stack.py`) lands under **Styling** instead — matching the iTerm2 / zsh pattern of "one bundle, one click".
- Bundled the maintainer's actual setup into the repo:
  - `config/vscode/extensions.txt` — extension IDs, one per line (no Excalidraw / Draw.io, per request).
  - `config/vscode/settings.json` — verbatim copy of `~/Library/Application Support/Code/User/settings.json`.
- The module installs every missing extension via `code --install-extension <id>` (skipping ones already present per `code --list-extensions`), then overwrites `settings.json` with the bundled file (backs up existing). Overrides via `VSCODE_EXTENSIONS_URL` / `VSCODE_SETTINGS_URL` env vars when needed.
- `--dry-run` flag: each module checks state, prints what it **would** do, then returns without touching the system. Useful to verify idempotency and inspect generated commands.
- `src/runtime.py` — module-level `Runtime` dataclass carrying global flags. `app.py` sets `runtime.dry_run` from `argparse` before the menu starts; modules read it on entry.
- Module: **XCode Command Line Tools** (`src/modules/xcode_cli.py`) under the System category. On install, triggers `xcode-select --install` (GUI dialog), shows an instruction panel, blocks on `press_any_key_to_continue`, then verifies. Required prerequisite for Homebrew.
- `src/safe.py` — `MAC_FRESH_SETUP_SAFE=1` hard guard. `mutating_run(cmd)` wraps subprocess calls that change state; `mutating_check(description)` precedes non-subprocess mutations (mkdir, file writes, chmod-on-new-files). When SAFE is set, either helper prints the blocked command and `SystemExit(1)`. Independent from `--dry-run` — dry-run is for inspection, SAFE is for defense in depth during local testing.
- `scripts/smoke.py` — single-command smoke test. Patches `subprocess.run` with a recorder, exports `MAC_FRESH_SETUP_SAFE=1`, sets `runtime.dry_run = True`, then runs every module under every category. Reports recorded calls per module and fails if any module attempts a mutating action. Run it with `uv run --with questionary --with rich python scripts/smoke.py` — this is the new step-1 of the ship sequence.

### Changed
- **XCode CLI detection** — replaced `pkgutil --pkg-info=com.apple.pkg.CLTools_Executables` with `xcode-select -p` + check that `<dev>/usr/bin/clang` exists. The pkgutil package id varies across macOS versions (and was returning false-negative on macOS Tahoe), the clang-existence check is uniformly reliable for both CLT-only and full-Xcode installs. On failure, the module now prints a diagnostic block (rc, stdout, stderr, dev-dir existence, clang existence) before asking the user to re-run.
- **XCode CLI wait flow** — replaced "press any key when install finishes" with active polling. After triggering `xcode-select --install`, the module displays a `rich.Progress` spinner and polls `xcode-select -p` + clang existence every 5 seconds (15-minute timeout). Removes a footgun where users hit a key before completing the GUI dialog, leaving CLT half-installed.
- **XCode CLI install path** — primary route is now `softwareupdate --install` (CLI, live progress visible to the user). The module touches the trigger file `/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress`, queries `softwareupdate --list` to find the latest `Command Line Tools for Xcode-*` label, and runs `sudo softwareupdate --install --no-scan --agree-to-license <label>` with stdout streaming live (download %, install %, completion). Falls back to `xcode-select --install` (GUI dialog) + polling only when softwareupdate has no CLT package available. Solves the "opaque spinner" problem reported on the macOS Tahoe VM.
- **XCode CLI dialog fallback bails on installer close** — the GUI fallback now polls `pgrep -x "Install Command Line Developer Tools"` alongside the CLT-installed check. If the installer process never starts (15s grace) or starts then exits without success (user cancelled or "not available from SWU" error), the loop returns failure immediately instead of spinning to 15-minute timeout.
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

[Unreleased]: https://github.com/lipex360x/mac-fresh-setup/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/lipex360x/mac-fresh-setup/releases/tag/v0.2.0
[0.1.0]: https://github.com/lipex360x/mac-fresh-setup/releases/tag/v0.1.0

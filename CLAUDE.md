# mac-fresh-setup

Interactive CLI to bootstrap a fresh macOS install — runs standalone via `uv` with no clone required.

## Invocation pattern (target)

```bash
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py"
```

## Stack

- Python 3.11+ with PEP 723 inline script metadata
- `questionary` for interactive single-select menus (hub-and-spoke pattern)
- `rich` for formatted output
- No external dependencies beyond what `uv` resolves inline

Reference implementation: [lipex360x/cct-netbeans-setup](https://github.com/lipex360x/cct-netbeans-setup) — same `uv run <url>` pattern.

## Source of truth

The setup steps are derived from gist `6b8e69af1b4a7a439dd1ca4baef735a7` (file `1 - Fresh Install.md`).
Fetch with: `gh gist view 6b8e69af1b4a7a439dd1ca4baef735a7`

## Structure

```
mac-fresh-setup/
├── setup.py                    # PEP 723 bootstrap — downloads tarball, runs app
├── src/
│   ├── app.py                  # main menu loop + preflight + argparse
│   ├── console.py              # rich Console singleton
│   ├── models.py               # Module / Category dataclasses
│   ├── runtime.py              # Runtime dataclass (dry_run flag)
│   ├── safe.py                 # mutating_run / mutating_check + SAFE mode
│   ├── categories.py           # CATEGORIES registry
│   └── modules/
│       ├── system/             # sudoers, xcode_cli, ssh_key
│       ├── package_manager/    # claude_code, homebrew_install, homebrew_packages, mise_runtimes
│       └── styling/            # iterm2_prefs, zsh_stack (+ internals: oh_my_zsh, spaceship, zshrc), vscode_stack
├── config/
│   ├── iterm2/com.googlecode.iterm2.plist   # bundled iTerm2 prefs (XML form)
│   ├── zsh/.zshrc                            # bundled zsh styling config
│   └── vscode/
│       ├── settings.json                     # bundled VSCode user settings
│       └── extensions.txt                    # extension IDs, one per line
├── scripts/smoke.py            # mocked-subprocess smoke test (ship sequence step 1)
├── docs/fresh-install.md       # source-of-truth gist mirrored locally
├── CHANGELOG.md
└── README.md
```

The bootstrap inserts `src/` at `sys.path[0]`, so modules import each other directly (`from console import console`, `from models import Module`). No top-level package name — there is only one app here, so no namespace is needed.

`setup.py` keeps PEP 723 deps and is the only file fetched by `uv run <url>`; everything else is downloaded as a tarball into a temp dir and imported at runtime.

## Current status

Published at https://github.com/lipex360x/mac-fresh-setup (public). Tag `v0.1.0` is the only release; `[Unreleased]` and intermediate untagged versions (0.1.x) track ongoing progress in CHANGELOG.

## Curated lists — how to add an item

The repo has four "pick what you want" pickers, all backed by a list of small frozen dataclasses. Adding a new option is one line in the list — no other code needs to change.

| File | Class | Required fields | Install dispatch |
|---|---|---|---|
| `src/modules/package_manager/homebrew_packages.py` | `Package` | `name`, `kind` (`"formula"` or `"cask"`), `description`, optional `cleanup_paths` (tuple of paths under `$HOME` to `rm -rf` after uninstall) | `brew install <name>` or `brew install --cask <name>` based on `kind`; on uninstall, also removes the cleanup_paths |
| `src/modules/package_manager/mise_runtimes.py` | `Runtime` | `title`, `spec` (e.g. `"node@lts"`), `description` | `mise use -g <spec>` |
| `config/vscode/extensions.txt` | (plain text) | one extension ID per line, `#` for comments | `code --install-extension <id>` (run by `vscode_stack`) |

Each picker queries the existing-state once before the prompt and greys out already-installed items via `questionary.Choice(..., disabled="installed")`. Order in the list = order in the menu.

Example — adding a new cask:

```python
Package("postman", "cask", "Postman API client (proprietary alternative to Bruno"),
```

Example — adding a new mise runtime:

```python
Runtime("Go latest", "go@latest", "Go toolchain — rolling release"),
```

That's it. No category change, no registration step, no test scaffolding required (the smoke runner picks it up automatically).

## Cross-platform model

The project is single-codebase, OS-aware. The Module dataclass carries a `platforms: frozenset[str]` field (`"darwin"`, `"linux"`, `"win32"`). The main menu filters categories+modules through `sys.platform` once at the top — downstream code never branches on the OS. Each module is "OS-pure": `homebrew_*` assumes brew, future `scoop_*` assumes scoop, `mysql`/`postgres`/`mise_runtimes`/`vscode_stack`/`claude_code`/`ssh_key` work the same everywhere because the underlying tools do.

Equivalence map (planned for Windows):

| Concept | macOS / Linux | Windows |
|---|---|---|
| Package manager | Homebrew (brew install / brew install --cask) | Scoop or winget |
| Privilege grant | sudoers NOPASSWD | (n/a — UAC is different model, likely skipped) |
| Dev toolchain | XCode CLT (clang, git, make, headers) | Git for Windows (bundles bash, git, curl, tar, unzip, ssh-keygen, openssl) |
| Terminal styling | iTerm2 plist | Windows Terminal settings.json |
| Shell stack | Oh-my-zsh + Spaceship + zinit | Oh-my-posh (works in PowerShell + git-bash) |
| `mise activate` line in shell init | `~/.zshrc` | `$PROFILE` for PowerShell, `~/.bashrc` for git-bash |
| Wrapper location | `~/.local/bin/<name>` | `~/.local/bin/<name>` + `<name>.cmd` shim (so PATH finds it from cmd/PowerShell) |

When OS-specific data does belong inside a universal module, use a small dispatch table at the module top — never an `if sys.platform` halfway through a function:

```python
ARCHIVE_EXT = {"darwin": "tar.gz", "linux": "tar.gz", "win32": "zip"}[sys.platform]
```

## Conventions

- Each module must be idempotent (check before acting)
- Each module must support `--dry-run`: after the idempotency check, if `runtime.dry_run` is true, print what would happen and `return` before any side effect
- Every mutating subprocess call goes through `safe.mutating_run` (not `subprocess.run`); every non-subprocess mutation (mkdir, write_text, chmod-on-new-files) is preceded by `safe.mutating_check("description")`. This makes `MAC_FRESH_SETUP_SAFE=1` a hard safety net independent of dry-run.
- Read-only subprocess calls (`sudo cat`, `xcode-select -p`, `pkgutil --pkg-info`, status queries) stay on plain `subprocess.run`.
- Interactive steps (`gh auth login`, `ssh-keygen` passphrase) require explicit user pause
- No shell `cd` between commands — use absolute paths (Bash tool resets cwd)
- Brew install uses `NONINTERACTIVE=1` to avoid prompts
- Sudoers writes validated via `visudo -cf` before being copied into `/etc/sudoers.d/`

## Ship sequence (every change)

Default flow for any code change in this repo:

1. **Test locally** — run the smoke test. It mocks `subprocess.run` and sets `MAC_FRESH_SETUP_SAFE=1` + `runtime.dry_run = True`, so it's guaranteed not to mutate the host:
   ```sh
   uv run --with questionary --with rich python scripts/smoke.py
   ```
   Expected tail line: `Smoke test OK — no module mutated the host.`
2. **Update CHANGELOG.md** if behavior changed — add under `[Unreleased]` with `### Added/Changed/Why`. Bump to a new untagged `0.x.y` section once the change consolidates.
3. **Update README.md** if invocation, flags, or user-visible features changed.
4. **Commit** with conventional message (`feat:`, `fix:`, `refactor:`, `docs:`, etc.).
5. **Push** to `origin/main`. Tag only on milestone releases (see `feedback_release_only_tags` in agent memory).

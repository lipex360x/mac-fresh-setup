# mac-fresh-setup

Interactive CLI to bootstrap a fresh macOS install. Runs standalone via `uv` — no clone, no global dependencies.

## Prerequisites

Install `uv` (Astral's Python package manager):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Reopen your terminal (or run `source $HOME/.local/bin/env`) so `uv` lands on your `PATH`.

Verify:

```sh
uv --version
```

## Usage

```sh
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py"
```

`uv` downloads `setup.py`, resolves the inline dependencies (PEP 723) and runs it. `setup.py` then fetches the rest of the source tree (`src/`) from a tarball into a temp directory and hands off to the interactive menu.

The menu is a hub: pick a **category**, then pick a **module** inside it, run it, return to the submenu. `← Back` returns to the main menu; `Exit` closes the app.

### Dry-run

Inspect what each module would do without making changes:

```sh
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py" -- --dry-run
```

The `--` separates `uv`'s flags from the script's flags. Each module prints the commands it would run, then returns without touching the system.

### Bypassing cache

Both `uv` and GitHub's raw CDN cache the script for a few minutes. If you just pushed a change and want the freshest copy, add `--refresh`:

```sh
uv run --refresh "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py"
```

If GitHub's CDN is still serving the old blob, append a cache-buster query (the URL still resolves):

```sh
uv run --refresh "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py?v=$RANDOM"
```

## Pinning to a tag

By default the bootstrap fetches the `main` branch. To run a specific release:

```sh
MAC_FRESH_SETUP_REF=v0.1.0 uv run --refresh "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py"
```

The env var controls only the tarball ref; the `setup.py` URL itself can stay on `main` (it's the same ~55-line bootstrap regardless of version).

## Modules available

**System**
- **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD`.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

All modules are idempotent — re-running is safe.

## Roadmap

Not implemented yet: XCode CLI, Homebrew + formulae/casks, Oh-my-zsh + Spaceship, asdf languages, VSCode extensions, git config + `gh auth`.

See `CHANGELOG.md` for the full history. Source reference: `docs/fresh-install.md`.

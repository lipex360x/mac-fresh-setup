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

`uv` downloads `setup.py`, resolves the inline dependencies (PEP 723) and runs it. An interactive menu appears — pick the modules you want (space to toggle, enter to confirm).

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

## Current stage (v0.1)

- **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD`.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

Modules are idempotent — re-running is safe.

## Roadmap

Not in this version: XCode CLI, Homebrew + formulae/casks, Oh-my-zsh + Spaceship, asdf languages, VSCode extensions, git config + `gh auth`.

Source reference: `docs/fresh-install.md`.

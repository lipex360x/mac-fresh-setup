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

## Current stage (v0.1)

- **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD`.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

Modules are idempotent — re-running is safe.

## Roadmap

Not in this version: XCode CLI, Homebrew + formulae/casks, Oh-my-zsh + Spaceship, asdf languages, VSCode extensions, git config + `gh auth`.

Source reference: `docs/fresh-install.md`.

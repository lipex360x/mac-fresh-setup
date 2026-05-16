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
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py" --dry-run
```

Each module prints the commands it would run, then returns without touching the system. Everything after the URL is passed straight to the script.

### Safe mode (defense-in-depth)

For local development or paranoid runs, set `MAC_FRESH_SETUP_SAFE=1`. Any state-changing subprocess call or non-subprocess mutation is blocked with a clear error and the script exits. Combine with `--dry-run` for the safest possible inspection:

```sh
MAC_FRESH_SETUP_SAFE=1 uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py" --dry-run
```

The smoke test (`scripts/smoke.py`) uses this together with a `subprocess.run` mock — that's how every change is validated locally before pushing.

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
- **XCode Command Line Tools** — installs Command Line Tools via `softwareupdate` (live progress) with `xcode-select --install` GUI dialog fallback; detection via `xcode-select -p` + clang existence.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

**Package manager**
- **Homebrew** — runs the official install script with `NONINTERACTIVE=1`, then appends `brew shellenv` to `~/.zprofile`.
- **Homebrew formulae** — checkbox menu of CLI tools (`mise`, `gh`); installs the selected ones via `brew install`.
- **Homebrew casks** — checkbox menu of GUI apps (`iterm2`); installs the selected ones via `brew install --cask`.

**Styling**
- **iTerm2 preferences** — downloads the bundled plist from `config/iterm2/com.googlecode.iterm2.plist` (override with `ITERM2_PREFS_URL`) and replaces `~/Library/Preferences/com.googlecode.iterm2.plist`. Backs up the existing file, then runs `killall cfprefsd`. Falls back to `~/Downloads/` with manual import instructions if direct write is blocked.
- **Oh-my-zsh** — runs the official installer with `RUNZSH=no CHSH=no KEEP_ZSHRC=yes`.
- **Spaceship theme** — clones `denysdovhan/spaceship-prompt` under `$ZSH_CUSTOM/themes` and symlinks the theme file.
- **Custom .zshrc** — replaces `~/.zshrc` with the bundled `config/zsh/.zshrc` (Spaceship + zinit plugins + mise activation; no aliases). Override with `ZSHRC_URL`.

### Exporting your iTerm2 prefs from another Mac

```sh
cp ~/Library/Preferences/com.googlecode.iterm2.plist /path/to/share/iterm2.plist
```

Upload that file to a gist or any HTTP location, then on the target machine:

```sh
export ITERM2_PREFS_URL="https://gist.githubusercontent.com/<you>/<hash>/raw/iterm2.plist"
uv run --refresh "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py?v=$RANDOM"
```

The Styling → iTerm2 preferences module will pick up the env var automatically.

All modules are idempotent — re-running is safe.

## Roadmap

Not implemented yet: Languages via mise (node/python/java/bun), Oh-my-zsh + Spaceship, VSCode extensions, git config + `gh auth`.

See `CHANGELOG.md` for the full history. Source reference: `docs/fresh-install.md`.

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
│   ├── app.py                  # main menu loop + preflight
│   ├── console.py              # rich Console singleton
│   ├── models.py               # Module / Category dataclasses
│   ├── categories.py           # CATEGORIES registry
│   └── modules/
│       ├── sudoers.py          # step: grant root access
│       └── ssh_key.py          # step: generate SSH key
├── docs/fresh-install.md       # source-of-truth gist mirrored locally
├── CHANGELOG.md
└── README.md
```

The bootstrap inserts `src/` at `sys.path[0]`, so modules import each other directly (`from console import console`, `from models import Module`). No top-level package name — there is only one app here, so no namespace is needed.

`setup.py` keeps PEP 723 deps and is the only file fetched by `uv run <url>`; everything else is downloaded as a tarball into a temp dir and imported at runtime.

## Current status

Published at https://github.com/lipex360x/mac-fresh-setup (public). Tag `v0.1.0` is the only release; `[Unreleased]` and intermediate untagged versions (0.1.x) track ongoing progress in CHANGELOG.

## Candidate modules (from gist)

System: sudoers NOPASSWD, XCode CLI, SSH key, git config, gh auth
Homebrew: install, formulae (asdf, gh, bun), casks (iterm2, vscode, intellij, docker, brave, bruno, beekeeper, fonts, aldente, betterdisplay, raycast)
Shell: oh-my-zsh, spaceship theme, zinit + plugins, custom .zshrc
Languages (via asdf): Java + Maven, Node LTS, Python
VSCode: extensions + user settings.json

Scope for v0.1 not yet decided — currently in planning conversation.

## Conventions

- Each module must be idempotent (check before acting)
- Interactive steps (`gh auth login`, `ssh-keygen` passphrase) require explicit user pause
- No shell `cd` between commands — use absolute paths (Bash tool resets cwd)
- Brew install uses `NONINTERACTIVE=1` to avoid prompts
- Sudoers writes validated via `visudo -cf` before being copied into `/etc/sudoers.d/`

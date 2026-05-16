# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

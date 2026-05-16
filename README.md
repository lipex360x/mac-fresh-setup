# mac-fresh-setup

> Interactive CLI to bootstrap a fresh macOS install. Runs standalone via `uv` — no clone, no global dependencies.

## Contents

- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Recommended order on a fresh Mac](#recommended-order-on-a-fresh-mac)
- [Modules available](#modules-available)
- [Runtime runbooks](#runtime-runbooks)
  - [Running PHP](#running-php)
  - [Running Java with Maven and Gradle](#running-java-with-maven-and-gradle)
- [Adding new items](#adding-new-items)
- [Bootstrap flags and overrides](#bootstrap-flags-and-overrides)
- [See also](#see-also)

## Prerequisites

Install `uv` (Astral's Python package manager):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Reopen your terminal (or run `source $HOME/.local/bin/env`) so `uv` lands on your `PATH`. Verify:

```sh
uv --version
```

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Quickstart

```sh
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py"
```

`uv` downloads `setup.py`, resolves the inline dependencies (PEP 723) and runs it. `setup.py` fetches the rest of `src/` from a tarball into a temp directory and hands off to the interactive menu. The menu is a hub: pick a **category**, then pick a **module** inside it, run it, return to the submenu. `← Back` returns to the main menu; `Exit` closes the app.

Inspect what each module would do without making changes:

```sh
uv run "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py" --dry-run
```

> [!TIP]
> Need the freshest copy after a push? Add `--refresh` and a cache-buster query — see [Bootstrap flags and overrides](#bootstrap-flags-and-overrides).

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Recommended order on a fresh Mac

1. System → Grant Root Access (so subsequent `sudo` doesn't prompt)
2. System → XCode Command Line Tools
3. System → SSH Key
4. Package manager → Claude Code (optional, but cheap)
5. Package manager → Homebrew
6. Package manager → Homebrew packages → Install (pick the apps + fonts you want)
7. Package manager → Mise runtimes → Install (pick runtimes)
8. Styling → iTerm2 preferences (needs Fira Code already from step 6)
9. Styling → Zsh stack
10. Styling → VSCode stack (needs `visual-studio-code` already from step 6)

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Modules available

**System**
- **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD` (validated via `visudo -cf`).
- **XCode Command Line Tools** — installs via `softwareupdate` (live progress) with `xcode-select --install` GUI dialog fallback; detection via `xcode-select -p` + clang existence.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

**Package manager**
- **Claude Code** — installs Anthropic's CLI via the official `curl https://claude.ai/install.sh | bash` route. No brew, no Node required.
- **Homebrew** — runs the official install script with `NONINTERACTIVE=1`, then appends `brew shellenv` to `~/.zprofile`.
- **Homebrew packages** — prompts **Install / Uninstall / Back**, then shows only the actionable items (install mode hides already-installed, uninstall mode hides not-installed). Formulae and casks live in the same list, casks tagged `[cask]`. Cask-specific uninstall cleanup paths are honoured (e.g. VSCode wipes `~/Library/Application Support/Code` etc.).
- **Mise runtimes** — same Install / Uninstall flow over `mise` runtimes: Node.js LTS, Bun latest, Java LTS (Temurin 25), Maven latest, Gradle latest, PHP 8.3.

**Styling**
- **iTerm2 preferences** — downloads the bundled plist from `config/iterm2/com.googlecode.iterm2.plist` and replaces `~/Library/Preferences/com.googlecode.iterm2.plist`. Backs up the existing file, runs `killall cfprefsd`.
- **Zsh stack** — installs Oh-my-zsh, the Spaceship theme, and the bundled `config/zsh/.zshrc` in one go.
- **VSCode stack** — installs the bundled extensions list (`config/vscode/extensions.txt`) and overwrites `settings.json` from `config/vscode/settings.json`.

All modules are idempotent — re-running is safe.

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Runtime runbooks

> [!IMPORTANT]
> After installing **any** runtime (PHP, Java, Node, Bun…), open a **new** terminal so `~/.zshrc` runs and `mise activate zsh` puts the shims on your `PATH`. `which <tool>` should report the mise shim at `~/.local/share/mise/shims/...`. The two runbooks below assume you've already done this.

### Running PHP

> [!WARNING]
> Mise installs PHP **by compiling it from source** via the `asdf-php` plugin. First install takes 5–10 minutes and needs C build tools.

#### 1. Install the build dependencies first

> [!NOTE]
> Skipping this step is the #1 cause of PHP compile failures mid-build. Run **before** picking PHP in the menu.

```sh
brew install autoconf bison re2c gd libsodium pkg-config libpq libzip libxml2 \
  openssl@3 libiconv libjpeg curl
```

#### 2. Install via the menu

Package manager → Mise runtimes → Install → check `PHP 8.3` → enter. Live `mise use -g php@8.3` output streams below.

#### 3. Verify

```sh
which php       # expected: /Users/you/.local/share/mise/shims/php
php --version   # expected: PHP 8.3.x (cli)
```

#### 4. Run something

```sh
php script.php                    # one-off script
php -a                            # REPL
php -S localhost:8000             # built-in dev server serving cwd at http://localhost:8000
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| Compile failed mid-build | Re-run the `brew install` block above, then run the Install option again to retry the build. |
| `php` not found after a successful install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| Wrong PHP version active | `mise current php` shows the global default; `mise use -g php@8.3` re-pins. |
| Need a different version | Edit `Runtime("PHP 8.3", "php@8.3", ...)` in `src/modules/package_manager/mise_runtimes.py` (e.g. `php@8.4`, `php@8.2`) and re-run the module. |

### Running Java with Maven and Gradle

Unlike PHP, Mise's Java install **does not compile from source** — it downloads the pre-built Temurin JDK tarball from Adoptium. First install takes ~1 minute. No brew prerequisites needed.

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Java LTS (Temurin 25)` (and optionally `Maven latest` / `Gradle latest`) → enter.

#### 2. Verify

```sh
which java        # expected: /Users/you/.local/share/mise/shims/java
java -version     # expected: openjdk version "25.x.x" ... + "Temurin-25..."
javac -version    # expected: javac 25.x.x
echo $JAVA_HOME   # expected: /Users/you/.local/share/mise/installs/java/temurin-25.x.x
```

`JAVA_HOME` is set automatically by `mise activate zsh` and is required by Maven, Gradle, IntelliJ, etc.

#### 3. Compile and run

JDK 11+ accepts source-file mode (no separate compile step):

```sh
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("hi from " + System.getProperty("java.version"));
    }
}
EOF

java Hello.java       # expected: hi from 25.x.x
```

Classic two-step:

```sh
javac Hello.java   # produces Hello.class
java Hello         # runs the class (no .class extension)
```

#### 4. With Maven

```sh
mvn --version                                  # confirms Maven sees JAVA_HOME

mvn archetype:generate \
  -DgroupId=com.example \
  -DartifactId=demo \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DinteractiveMode=false

cd demo
mvn package                                    # produces target/demo-1.0-SNAPSHOT.jar
java -cp target/demo-1.0-SNAPSHOT.jar com.example.App
```

#### 5. With Gradle

```sh
gradle --version                               # confirms Gradle sees JAVA_HOME

mkdir demo && cd demo
gradle init --type java-application --dsl groovy --no-incubating-report

gradle run                                     # build + run the generated App
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `java` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| `JAVA_HOME` empty | `mise activate zsh` isn't running. Confirm `eval "$(mise activate zsh)"` is in `~/.zshrc` (the bundled file ships with it). |
| Maven/Gradle reports the wrong Java | `mise current java` shows the global default; `mise use -g java@temurin-25` re-pins. Project-local override: drop a `.mise.toml` with `[tools] java = "temurin-25"`. |
| Need another distribution | Edit `Runtime("Java LTS (Temurin 25)", "java@temurin-25", ...)` in `mise_runtimes.py` to e.g. `java@corretto-25`, `java@zulu-25`, `java@graalvm-25`. |
| Want a REPL without writing files | `jshell` opens it (`/exit` to leave). |

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Adding new items

Each picker is backed by a small frozen dataclass list — adding an option is one line:

```python
# src/modules/package_manager/homebrew_packages.py
Package("postman", "cask", "Postman API client"),
Package("docker-desktop", "cask", "...", cleanup_paths=("Library/Containers/com.docker.docker",)),

# src/modules/package_manager/mise_runtimes.py
Runtime("Go latest", "go@latest", "Go toolchain"),
```

The full pattern is documented in `CLAUDE.md` under *Curated lists — how to add an item*.

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Bootstrap flags and overrides

Everything after the URL is passed straight to the script.

| Flag / env var | Where | What it does |
|----------------|-------|--------------|
| `--dry-run` | script | Each module prints what it would run without touching the system. |
| `MAC_FRESH_SETUP_SAFE=1` | env | Hard guard: any mutating subprocess call or file write aborts with a clear error. Combine with `--dry-run` for the safest possible inspection. |
| `--refresh` | `uv run` | `uv` re-downloads `setup.py` instead of using its cache. |
| `?v=$RANDOM` query in URL | URL | Cache-busts the GitHub raw CDN when the new push hasn't propagated yet. |
| `MAC_FRESH_SETUP_REF=<ref>` | env | Pins the tarball ref. Default `main`. Use a tag like `v0.1.0` (the only tag today) to freeze the source. |
| `ITERM2_PREFS_URL` | env | Override the iTerm2 plist source (defaults to the bundled `config/iterm2/com.googlecode.iterm2.plist`). |
| `ZSHRC_URL` | env | Override the `.zshrc` source. |
| `VSCODE_EXTENSIONS_URL` | env | Override the VSCode extensions list source. |
| `VSCODE_SETTINGS_URL` | env | Override the VSCode `settings.json` source. |

Example combining several:

```sh
MAC_FRESH_SETUP_SAFE=1 \
  uv run --refresh "https://raw.githubusercontent.com/lipex360x/mac-fresh-setup/main/setup.py?v=$RANDOM" \
  --dry-run
```

The smoke test (`scripts/smoke.py`) uses `MAC_FRESH_SETUP_SAFE=1` together with a `subprocess.run` mock — that's how every change is validated locally before pushing.

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## See also

| File | Purpose |
|------|---------|
| `CHANGELOG.md` | Full history. Versions are progress checkpoints; git tags only for milestones. |
| `CLAUDE.md` | Repo conventions, ship sequence, curated-list pattern. |
| `docs/fresh-install.md` | Source-of-truth gist mirrored locally. |

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

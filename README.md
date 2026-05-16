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
- **Grant Root Access** — adds the current user to `/etc/sudoers.d` with `NOPASSWD` (validated via `visudo -cf`).
- **XCode Command Line Tools** — installs Command Line Tools via `softwareupdate` (live progress) with `xcode-select --install` GUI dialog fallback; detection via `xcode-select -p` + clang existence.
- **SSH Key** — generates `~/.ssh/id_rsa` (RSA 4096) if missing, fixes permissions, prints the public key to paste into GitHub.

**Package manager**
- **Claude Code** — installs Anthropic's CLI via the official `curl https://claude.ai/install.sh | bash` route. No brew, no Node required — runs on a fresh Mac.
- **Homebrew** — runs the official install script with `NONINTERACTIVE=1`, then appends `brew shellenv` to `~/.zprofile`.
- **Homebrew packages** — prompts **Install / Uninstall / Back**, then shows only the actionable items (install mode hides already-installed, uninstall mode hides not-installed). Formulae and casks live in the same list, casks tagged `[cask]`. Cask-specific uninstall cleanup paths are honoured (e.g. VSCode wipes `~/Library/Application Support/Code` etc.).
- **Mise runtimes** — same Install / Uninstall flow over `mise` runtimes: Node.js LTS, Bun latest, Java LTS (Temurin 25), Maven latest, Gradle latest, PHP 8.3.

**Styling**
- **iTerm2 preferences** — downloads the bundled plist from `config/iterm2/com.googlecode.iterm2.plist` (override with `ITERM2_PREFS_URL`) and replaces `~/Library/Preferences/com.googlecode.iterm2.plist`. Backs up the existing file, runs `killall cfprefsd`.
- **Zsh stack** — installs Oh-my-zsh, the Spaceship theme, and the bundled `config/zsh/.zshrc` in one go.
- **VSCode stack** — installs the bundled extensions list (`config/vscode/extensions.txt`) and overwrites `settings.json` from `config/vscode/settings.json`. Overrides via `VSCODE_EXTENSIONS_URL` / `VSCODE_SETTINGS_URL`.

All modules are idempotent — re-running is safe.

## Recommended order on a fresh Mac

1. System → Grant Root Access (so subsequent `sudo` doesn't ask for a password)
2. System → XCode Command Line Tools
3. System → SSH Key
4. Package manager → Claude Code (optional, but cheap)
5. Package manager → Homebrew
6. Package manager → Homebrew packages → Install (pick the apps + fonts you want)
7. Package manager → Mise runtimes → Install (pick runtimes)
8. Styling → iTerm2 preferences (needs Fira Code already from step 6)
9. Styling → Zsh stack
10. Styling → VSCode stack (needs visual-studio-code already from step 6)

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

## Running PHP after installing it

`mise use -g php@8.3` (Mise runtimes module) installs PHP **by compiling it from source** via the `asdf-php` plugin. There is no Homebrew bottle in this path — first install takes 5–10 minutes and needs C build tools.

### 1. Make sure the build dependencies are present

```sh
brew install autoconf bison re2c gd libsodium pkg-config libpq libzip libxml2 \
  openssl@3 libiconv libjpeg curl
```

Without these the build will fail mid-compile with cryptic linker errors. (We don't auto-install them yet — open an issue if you'd like that automated.)

### 2. Install via the menu

Package manager → Mise runtimes → Install → check `PHP 8.3` → enter. Live `mise use -g php@8.3` output streams below; wait for it.

### 3. Pick up `php` in the shell

Open a **new** terminal so `~/.zshrc` runs and `mise activate zsh` puts the shims on `PATH`. Verify:

```sh
which php
# expected: /Users/you/.local/share/mise/shims/php

php --version
# expected: PHP 8.3.x (cli)
```

If `which php` still shows nothing or an old path, check that `eval "$(mise activate zsh)"` is in `~/.zshrc` (the bundled config does this) and that you opened a fresh shell.

### 4. Run something

```sh
# one-off script
php script.php

# REPL
php -a

# built-in dev server serving the current directory at http://localhost:8000
php -S localhost:8000
```

### Troubleshooting

- **Compile failed**: rerun the `brew install` from step 1, then `mise install php@8.3` (re-run the menu's Install option — it'll re-trigger the build).
- **`php` not found after a successful install**: you forgot to reopen the shell. Either open a new terminal or run `source ~/.zshrc`.
- **Wrong PHP version active**: `mise current php` shows the global default, `mise use -g php@8.3` re-pins it.
- **Need a different version**: edit `Runtime("PHP 8.3", "php@8.3", ...)` in `mise_runtimes.py` to whatever you want (`php@8.4`, `php@8.2`, etc.) and re-run the module.

## Running Java (with Maven / Gradle) after installing it

Unlike PHP, Mise's Java install **does not compile from source** — it downloads the pre-built Temurin JDK tarball from Adoptium. First install takes ~1 minute.

### 1. Install

Package manager → Mise runtimes → Install → check `Java LTS (Temurin 25)` (and optionally `Maven latest` / `Gradle latest`) → enter. No brew prerequisites needed.

### 2. Pick up `java` in the shell

Open a **new** terminal so `~/.zshrc` runs and `mise activate zsh` puts the shims on `PATH`. Verify:

```sh
which java
# expected: /Users/you/.local/share/mise/shims/java

java -version
# expected: openjdk version "25.x.x" 2025-09-... + "Temurin-25..."

javac -version
# expected: javac 25.x.x

echo $JAVA_HOME
# expected: /Users/you/.local/share/mise/installs/java/temurin-25.x.x
```

`JAVA_HOME` is set automatically by `mise activate zsh` — required by Maven, Gradle, IntelliJ, etc.

### 3. Compile and run

**One-off file** (JDK 11+ accepts source-file mode, no separate compile step):

```sh
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("hi from " + System.getProperty("java.version"));
    }
}
EOF

java Hello.java
# expected: hi from 25.x.x
```

Or the classic two-step:

```sh
javac Hello.java   # produces Hello.class
java Hello         # runs the class (no .class extension)
```

### 4. With Maven

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

### 5. With Gradle

```sh
gradle --version                               # confirms Gradle sees JAVA_HOME

mkdir demo && cd demo
gradle init --type java-application --dsl groovy --no-incubating-report

gradle run                                     # build + run the generated App
```

### Troubleshooting

- **`java` not found after install**: you forgot to reopen the shell. Open a new terminal or `source ~/.zshrc`.
- **`JAVA_HOME` empty**: `mise activate zsh` isn't running. Confirm `eval "$(mise activate zsh)"` is in `~/.zshrc` (the bundled file ships with it).
- **Maven/Gradle reports the wrong Java**: `mise current java` shows the global default, `mise use -g java@temurin-25` re-pins. Project-local override: drop a `.mise.toml` in the project root with `[tools] java = "temurin-25"`.
- **Need another distribution**: edit `Runtime("Java LTS (Temurin 25)", "java@temurin-25", ...)` in `src/modules/package_manager/mise_runtimes.py` to e.g. `java@corretto-25`, `java@zulu-25`, `java@graalvm-25`, etc.
- **Compile/run a quick example without writing files**: `jshell` opens the REPL (`exit` to leave).

## See also

- `CHANGELOG.md` — full history (versions are progress checkpoints; git tags only for milestones).
- `CLAUDE.md` — repo conventions, ship sequence, curated-list pattern.
- `docs/fresh-install.md` — source-of-truth gist mirrored locally.

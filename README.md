# mac-fresh-setup

> Interactive CLI to bootstrap a fresh macOS install. Runs standalone via `uv` — no clone, no global dependencies.

## Contents

- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Recommended order on a fresh Mac](#recommended-order-on-a-fresh-mac)
- [Modules available](#modules-available)
- [Runtime runbooks](#runtime-runbooks)
  - [Running Node.js](#running-nodejs)
  - [Running Bun](#running-bun)
  - [Running Java](#running-java)
  - [Running Maven](#running-maven)
  - [Running Gradle](#running-gradle)
  - [Running PHP](#running-php)
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

**Databases**
- **MySQL (standalone tarball)** — downloads the official MySQL 8.4 tarball into `~/.local/share/mac-fresh-setup/mysql/`. No brew, no sudo, no Docker. Installs four wrappers in `~/.local/bin/` for day-to-day control: `mysql-up` (`-p PORT`, `--pass PASS`), `mysql-down`, `mysql-status`, `mysql-cli`. Uninstall has two flavours: **keep data** (only removes binaries) or **wipe everything**.
- **PostgreSQL (standalone binaries)** — same shape as MySQL but built from the EDB binary distribution (no compile, no brew). Installs to `~/.local/share/mac-fresh-setup/postgres/`. Wrappers in `~/.local/bin/`: `postgres-up` (`-p PORT`, `--pass PASS`), `postgres-down`, `postgres-status`, `postgres-cli`. Trust auth on first install (`postgres` superuser, no password); pass `--pass` to switch to md5 auth.

All modules are idempotent — re-running is safe.

<div align="right"><a href="#mac-fresh-setup">↑ Back to top</a></div>

## Runtime runbooks

> [!IMPORTANT]
> After installing **any** runtime (Node, Bun, Java, Maven, Gradle, PHP…), open a **new** terminal so `~/.zshrc` runs and `mise activate zsh` puts the shims on your `PATH`. `which <tool>` should report the mise shim at `~/.local/share/mise/shims/...`. All runbooks below assume you've already done this.

### Running Node.js

Mise installs Node.js from prebuilt binaries — fast (~30 s) and no compile.

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Node.js LTS` → enter.

#### 2. Verify

```sh
which node       # expected: /Users/you/.local/share/mise/shims/node
node --version   # expected: v22.x.x (or whatever the current LTS major is)
npm --version    # ships with Node
npx --version    # ships with Node
```

#### 3. Run something

```sh
node script.js                                 # one-off script
node                                           # REPL
node --eval "console.log(2 + 2)"               # one-liner

# tiny dev server
node --eval "require('http').createServer((_, r)=>r.end('hi')).listen(3000)"

# scaffold a new package
npm init -y && npm install --save-dev typescript
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `node` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| `npm` install fails on a global package | Mise's Node shim is per-user — never use `sudo npm install -g`. Just `npm install -g <pkg>`. |
| Need a specific Node major (e.g. 20) | `mise use -g node@20` from the terminal; or edit the `Runtime` entry to `node@20` and re-run the module. |
| Project pinning | Drop a `.mise.toml` in the project with `[tools] node = "lts"` or a specific version. |

### Running Bun

Mise installs Bun from a prebuilt binary — fastest of the runtimes (~10 s).

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Bun latest` → enter.

#### 2. Verify

```sh
which bun        # expected: /Users/you/.local/share/mise/shims/bun
bun --version    # expected: 1.x.x
```

#### 3. Run something

Bun is a Node-compatible runtime, package manager, bundler, and test runner. Single binary:

```sh
bun script.ts                                  # runs TypeScript directly, no compile step
bun script.js
bun repl

bun init                                       # scaffold a project
bun add hono                                   # add a dependency
bun run dev                                    # run a package.json script

bun test                                       # run tests
bun build ./index.ts --outdir ./dist           # bundle for prod
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `bun` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| `npm install` style command | Bun's equivalent is `bun add <pkg>` (or `bun install` to materialise `package.json`). |
| Bun and Node both installed — which wins | Whichever runs the script. `bun script.ts` uses Bun; `node script.ts` (with `tsx` or `ts-node`) uses Node. They don't conflict. |
| Need an older Bun | Edit the `Runtime` entry to `bun@1.1.x` and re-run the module. |

### Running Java

> [!NOTE]
> **Maven** and **Gradle** are separate Mise entries with their own runbooks below ([Running Maven](#running-maven), [Running Gradle](#running-gradle)) — install them through the same picker. Both depend on Java being set up first.

Unlike PHP, Mise's Java install **does not compile from source** — it downloads the pre-built Temurin JDK tarball from Adoptium. First install takes ~1 minute. No brew prerequisites needed.

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Java LTS (Temurin 25)` → enter.

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

Want a REPL without writing files: `jshell` (`/exit` to leave).

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `java` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| `JAVA_HOME` empty | `mise activate zsh` isn't running. Confirm `eval "$(mise activate zsh)"` is in `~/.zshrc` (the bundled file ships with it). |
| Wrong Java reported by Maven/Gradle/IntelliJ | `mise current java` shows the global default; `mise use -g java@temurin-25` re-pins. Project-local override: drop a `.mise.toml` with `[tools] java = "temurin-25"`. |
| Need another distribution | Edit `Runtime("Java LTS (Temurin 25)", "java@temurin-25", ...)` in `mise_runtimes.py` to e.g. `java@corretto-25`, `java@zulu-25`, `java@graalvm-25`. |

### Running Maven

> [!NOTE]
> Maven needs Java. Install it first via the [Java runbook](#running-java).

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Maven latest` → enter.

#### 2. Verify

```sh
which mvn       # expected: /Users/you/.local/share/mise/shims/mvn
mvn --version   # confirms version + the JAVA_HOME it sees
```

The bottom of `mvn --version` should reference your mise Java install (`/Users/you/.local/share/mise/installs/java/temurin-25.x.x`).

#### 3. Scaffold and build a project

```sh
mvn archetype:generate \
  -DgroupId=com.example \
  -DartifactId=demo \
  -DarchetypeArtifactId=maven-archetype-quickstart \
  -DinteractiveMode=false

cd demo
mvn package                                                  # produces target/demo-1.0-SNAPSHOT.jar
java -cp target/demo-1.0-SNAPSHOT.jar com.example.App
```

Useful goals:

```sh
mvn compile                                                  # compile sources only
mvn test                                                     # run unit tests
mvn package                                                  # build the jar
mvn clean install                                            # full rebuild + install to ~/.m2/repository
mvn dependency:tree                                          # show resolved dependencies
mvn versions:display-dependency-updates                      # find outdated deps
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `mvn` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| `mvn --version` reports a different JDK | `mise current java` not set, or `JAVA_HOME` overridden by something else in your shell init. Run `mise use -g java@temurin-25`, reopen the shell. |
| `Could not find or load main class` | Forgot to `mvn package` after editing; or the `-cp` argument doesn't point at the freshly built jar. |
| Slow first build | Maven downloads its plugin/dependency tree into `~/.m2/repository` on first use — that's normal. |

### Running Gradle

> [!NOTE]
> Gradle needs Java. Install it first via the [Java runbook](#running-java).

#### 1. Install via the menu

Package manager → Mise runtimes → Install → check `Gradle latest` → enter.

#### 2. Verify

```sh
which gradle       # expected: /Users/you/.local/share/mise/shims/gradle
gradle --version   # confirms version + the JVM it sees
```

#### 3. Scaffold and build a project

```sh
mkdir demo && cd demo
gradle init --type java-application --dsl groovy --no-incubating-report
gradle run                                                   # builds + runs the generated App
```

Useful tasks:

```sh
gradle build                                                 # full build + tests + jar
gradle test                                                  # run unit tests
gradle run                                                   # run the application (java-application template)
gradle clean                                                 # remove build/
gradle tasks                                                 # list all available tasks
gradle dependencies                                          # full dependency tree
```

#### Troubleshooting

| Symptom | Fix |
|---------|-----|
| `gradle` not found after install | You forgot to reopen the shell — see the IMPORTANT admonition above. |
| Gradle daemon issues / hung build | `gradle --stop` kills daemons; rerun the task. |
| Project uses the wrapper (`./gradlew`) | Use the project's `./gradlew` instead of the system `gradle` — the wrapper pins the exact Gradle version per project. The system `gradle` is for `gradle init` and ad-hoc tasks. |
| Slow first run | Gradle downloads its distribution + plugin cache into `~/.gradle/` on first use — that's normal. |

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

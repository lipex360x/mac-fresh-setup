## MacOS Settings

#### Orka

[Download](https://github.com/macstadium/orka-desktop/releases)

[Docs](https://github.com/macstadium/orka-images?tab=readme-ov-file)

* Tahoe Image no SIP (Pull from OCI Registry): `ghcr.io/macstadium/orka-images/tahoe:no-sip`

---

* Keyboard: US International PC

#### Grant Root access

> echo "$(whoami) ALL=(ALL) NOPASSWD:ALL" | sudo tee /private/etc/sudoers.d/$(whoami) > /dev/null && sudo tail /private/etc/sudoers.d/$(whoami)


#### SSH Key

> ssh-keygen -t rsa -b 4096

---

#### [Brew](https://formulae.brew.sh/)

> /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

> echo '# Set PATH, MANPATH, etc., for Homebrew.' >> $HOME/.zprofile

> echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile

> eval "$(/opt/homebrew/bin/brew shellenv)"

* Apps

```sh
brew install \
asdf \
oven-sh/bun/bun \
gh
```

```sh
brew install --cask \
iterm2 \
visual-studio-code \
intellij-idea-ce \
docker-desktop \
bruno \
the-unarchiver \
font-fira-code \
mockoon \
beekeeper-studio \
bitwarden \
aldente \
betterdisplay \
raycast \
orka-desktop
```

---

#### Oh-my-zsh

> sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

- [.zshrc](https://gist.github.com/lipex360x/cfe57f9cbef90ed7e06c2b0817a82909#file-2-zshrc) file

---

#### ZSH Spaceship Theme

> sudo git clone https://github.com/denysdovhan/spaceship-prompt.git "$ZSH_CUSTOM/themes/spaceship-prompt"

> sudo ln -s "$ZSH_CUSTOM/themes/spaceship-prompt/spaceship.zsh-theme" "$ZSH_CUSTOM/themes/spaceship.zsh-theme"

---

#### Git Config

> git config --global user.name "USER NAME"

> git config --global user.email "USER EMAIL"

> cd ~/.ssh && more id_rsa.pub && cd

> chmod 400 ~/.ssh/id_rsa

* GitHub test Connect
> ssh -T git@github.com

> gh auth login

---

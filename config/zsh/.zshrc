# DEFAULT CONFIGS
export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="spaceship"

SPACESHIP_PROMPT_ORDER=(
  user          # Username section
  dir           # Current directory section
  host          # Hostname section
  time          # Time stamps section
  git           # Git section (git_branch + git_status)
  hg            # Mercurial section (hg_branch  + hg_status)
  exec_time     # Execution time
  line_sep      # Line break
  jobs          # Background jobs indicator
  exit_code     # Exit code section
  char          # Prompt character
)

SPACESHIP_USER_SHOW=always
SPACESHIP_USER_COLOR=blue
SPACESHIP_TIME_SHOW=true
SPACESHIP_TIME_COLOR=green
SPACESHIP_PROMPT_ADD_NEWLINE=false
SPACESHIP_CHAR_SYMBOL="❯"
SPACESHIP_CHAR_SUFFIX=" "

DISABLE_AUTO_TITLE="true"
_set_terminal_title() {
  [[ -n "$TMUX" ]] && return
  printf '\033]0;%s\007' "${PWD##*/}"
}
precmd_functions+=(_set_terminal_title)
plugins=(git ssh-agent)

source $ZSH/oh-my-zsh.sh

### ZINIT
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
    print -P "%F{33} %F{220}Installing %F{33}ZDHARMA-CONTINUUM%F{220} Initiative Plugin Manager (%F{33}zdharma-continuum/zinit%F{220})…%f"
    command mkdir -p "$HOME/.local/share/zinit" && command chmod g-rwX "$HOME/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "$HOME/.local/share/zinit/zinit.git" && \
        print -P "%F{33} %F{34}Installation successful.%f%b" || \
        print -P "%F{160} The clone has failed.%f%b"
fi

source "$HOME/.local/share/zinit/zinit.git/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit

zinit light zdharma-continuum/fast-syntax-highlighting
zinit light zsh-users/zsh-autosuggestions
zinit light zsh-users/zsh-completions

### MISE (polyglot runtime manager — replaces asdf)
if command -v mise &>/dev/null; then
  eval "$(mise activate zsh)"
fi

export PATH="$HOME/.local/bin:$PATH"

### CLAUDE CODE
alias cc='claude --dangerously-skip-permissions'

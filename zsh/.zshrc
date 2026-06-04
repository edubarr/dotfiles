# 1) History
HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000
SAVEHIST=10000

setopt APPEND_HISTORY
setopt INC_APPEND_HISTORY
setopt SHARE_HISTORY
setopt HIST_FCNTL_LOCK

setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_REDUCE_BLANKS
setopt HIST_VERIFY
setopt EXTENDED_HISTORY

# 2) Zinit bootstrap
if [[ ! -e ~/.zinit/bin/zinit.zsh ]]; then
  git clone -q --depth=1 https://github.com/zdharma-continuum/zinit.git ~/.zinit/bin
fi
source ~/.zinit/bin/zinit.zsh

# 3) Completion
autoload -Uz compinit
compinit -C

# 4) Plugins
ZSH_AUTOSUGGEST_MANUAL_REBIND=1
zinit light zsh-users/zsh-autosuggestions

eval "$(starship init zsh)"

# Replay completion additions from plugins (after plugins are loaded)
zinit cdreplay -q

# Bind autosuggest widgets after other widgets are in place
_zsh_autosuggest_bind_widgets

# Syntax highlighting must be last
zinit light zsh-users/zsh-syntax-highlighting

# 5) PATH (dedupe + order)
typeset -U path PATH
path=(
  "$HOME/bin"
  "$HOME/.local/bin"
  "$HOME/go/bin"
  "$HOME/.opencode/bin"
  "$HOME/.bun/bin"
  $path
)

# 6) mise
command -v mise >/dev/null && eval "$(mise activate zsh)"

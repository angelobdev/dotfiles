# Every zsh reads this first, login and scripts included, so it stays silent. The rest lives in ~/.config/zsh.
export ZDOTDIR=${XDG_CONFIG_HOME:-$HOME/.config}/zsh
# The desktop commands (desktop-*) and user tools, once.
typeset -U path
path=("$HOME/.local/bin" $path)

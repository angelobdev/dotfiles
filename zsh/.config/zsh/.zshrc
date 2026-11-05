# Interactive zsh: Powerlevel10k (lean, the ANSI colors of the desktop theme), zsh-autocomplete,
# autosuggestions, syntax highlighting, fzf, zoxide, eza and bat. install-desktop.py (core) installs them;
# Powerlevel10k and zsh-autocomplete are pinned clones under ~/.local/share/zsh/plugins.

# Powerlevel10k instant prompt: keep it first. Anything that asks for input goes above it.
if [[ -r ${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh ]]; then
    source ${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh
fi

plugins=${XDG_DATA_HOME:-$HOME/.local/share}/zsh/plugins

# History, shared between open shells.
HISTFILE=${XDG_STATE_HOME:-$HOME/.local/state}/zsh/history
HISTSIZE=50000
SAVEHIST=50000
[[ -d ${HISTFILE:h} ]] || mkdir -p ${HISTFILE:h}
setopt extended_history share_history hist_ignore_all_dups hist_ignore_space hist_reduce_blanks
setopt auto_cd interactive_comments no_beep
bindkey -e

# zsh-autocomplete runs compinit itself, so nothing here calls it; it has to come before any compdef.
[[ -r $plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh ]] &&
    source $plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh

# The distribution's plugins: Fedora's folders first, then Arch's.
if [[ -r /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]]; then
    source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
elif [[ -r /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]]; then
    source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
fi

# fzf: Ctrl+R history, Ctrl+T files, Alt+C directories. After zsh-autocomplete, so Ctrl+R is fzf's.
if [[ -r /usr/share/fzf/shell/key-bindings.zsh ]]; then
    source /usr/share/fzf/shell/key-bindings.zsh
elif [[ -r /usr/share/fzf/key-bindings.zsh ]]; then
    source /usr/share/fzf/key-bindings.zsh
fi

# zoxide: z <part of a path> jumps to the directories used most; zi picks one with fzf.
(( $+commands[zoxide] )) && eval "$(zoxide init zsh)"

# eza and bat in place of ls and cat; icons come from kitty's built-in Nerd Font symbols.
if (( $+commands[eza] )); then
    alias ls='eza --group-directories-first --icons=auto'
    alias ll='eza -l --group-directories-first --icons=auto --git'
    alias la='eza -la --group-directories-first --icons=auto --git'
    alias tree='eza --tree --icons=auto'
fi
# Without a terminal (pipes, redirects) bat prints the file as is, like cat.
(( $+commands[bat] )) && alias cat='bat --paging=never'

[[ -r $plugins/powerlevel10k/powerlevel10k.zsh-theme ]] && source $plugins/powerlevel10k/powerlevel10k.zsh-theme
[[ -r $ZDOTDIR/p10k.zsh ]] && source $ZDOTDIR/p10k.zsh

# Last: it wraps the widgets every plugin above defined.
if [[ -r /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
    source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
elif [[ -r /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]]; then
    source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
fi

# Machine-specific additions, outside the repository.
[[ -r $ZDOTDIR/local.zsh ]] && source $ZDOTDIR/local.zsh

# Powerlevel10k: the upstream lean style in 8 colors, so the prompt takes the ANSI palette of the desktop theme
# (kitty.conf follows it). Only the differences from upstream are here.
source ${XDG_DATA_HOME:-$HOME/.local/share}/zsh/plugins/powerlevel10k/config/p10k-lean-8colors.zsh

# The clock in hours and minutes, at the end of the right prompt.
typeset -g POWERLEVEL9K_TIME_FORMAT='%D{%H:%M}'
(( ${POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS[(Ie)time]} )) || POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS+=(time)

(( ! $+functions[p10k] )) || p10k reload

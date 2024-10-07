#!/bin/bash

#################################################################################
#                                                                               #
#   This script has been written by angelobdev                                  #
#   It should be used in a properly configured Hyprland environment.            #
#                                                                               #
#   Look at the full configuration here: https://github.com/angelobdev/dotfiles #
#                                                                               #
#   The project (as well as this script) goes under the GNU GPLv3 LICENSE.      #
#                                                                               #
#################################################################################

CONFIG_FILES="$HOME/.config/waybar/config.jsonc $HOME/.config/waybar/modules.jsonc $HOME/.config/waybar/style.css"

trap "killall waybar" EXIT

while true; do
    nohup waybar &> /dev/null &
    inotifywait -e create,modify $CONFIG_FILES
    killall waybar
done

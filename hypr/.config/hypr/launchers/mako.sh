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

CONFIG_FILES="$HOME/.config/mako/config"

nohup mako &> /dev/null &

while true; do
    inotifywait -e create,modify $CONFIG_FILES
    makoctl reload
done

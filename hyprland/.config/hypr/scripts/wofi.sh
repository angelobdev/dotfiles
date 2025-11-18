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

killall wofi
# wofi --show drun --allow-images -a -i --prompt "Search..." --color "$HOME/.cache/wal/colors"
wofi --show drun --allow-images -a -i --prompt "Search..."
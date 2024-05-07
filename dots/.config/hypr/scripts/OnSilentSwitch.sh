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

silent_file="$HOME/.config/hypr/settings/silent"

if [[ -f "$silent_file" ]]; then
	rm "$silent_file"
	makoctl mode -r do-not-disturb
else
	touch "$silent_file"
	makoctl mode -a do-not-disturb
fi

dunstctl set-paused toggle

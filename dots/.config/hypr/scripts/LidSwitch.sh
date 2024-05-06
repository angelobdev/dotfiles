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

lid_closed=$(cat /proc/acpi/button/lid/LID0/state | grep closed)

if [[ $lid_closed ]]; then
	# If the lid is closed...
	monitors_count=$(hyprctl monitors | grep "Monitor" | wc -l)

	if [[ $monitors_count > 1 ]]; then
		# If another monitor is connected -> switch off the eDP-1
		hyprctl keyword monitor "eDP-1, disable"
	else
		# Otherwise suspend
		systemctl suspend
	fi
else
	# If the lid is opened...
	hyprctl keyword monitor "eDP-1, 2880x1800@60, 1920x0, 2"
fi

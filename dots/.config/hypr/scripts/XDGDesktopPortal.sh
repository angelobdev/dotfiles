#!/usr/bin/env bash

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

sleep 1

killall -e xdg-desktop-portal-hyprland
killall xdg-desktop-portal

/usr/lib/xdg-desktop-portal-hyprland &

sleep 2

/usr/lib/xdg-desktop-portal &

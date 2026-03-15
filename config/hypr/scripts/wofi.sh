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

# Resolve wofi binary safely
WOFI_CMD="${WOFI_CMD:-$(command -v wofi || echo /run/current-system/sw/bin/wofi)}"

# Kill existing instances
pkill -x wofi || true

# Launch wofi
exec "$WOFI_CMD" --show drun --allow-images -a -i --prompt "Search..." --normal-window
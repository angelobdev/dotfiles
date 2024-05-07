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

CONFIG_DIR="$HOME/.config"
DARK_MODE_FILE="$CONFIG_DIR/hypr/settings/dark"
LIGHT_MODE_FILE="$CONFIG_DIR/hypr/settings/light"

if [[ -f $DARK_MODE_FILE ]]; then
	
	# DARK MODE -> LIGHT MODE
	#echo "You're in dark mode..."
	#echo "Switching to light..."

	mv $DARK_MODE_FILE $LIGHT_MODE_FILE
	gsettings set org.gnome.desktop.interface color-scheme 'prefer-light'
	sed -i 's/darker/airy/' $CONFIG_DIR/qt5ct/qt5ct.conf
	sed -i 's/darker/airy/' $CONFIG_DIR/qt6ct/qt6ct.conf

	#echo "Done!"

elif [[ -f $LIGHT_MODE_FILE ]]; then

	# LIGHT MODE -> DARK MODE
	#echo "You're in light mode..."
	#echo "Switching to dark..."

	mv $LIGHT_MODE_FILE $DARK_MODE_FILE
	gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
	sed -i 's/airy/darker/' $CONFIG_DIR/qt5ct/qt5ct.conf
	sed -i 's/airy/darker/' $CONFIG_DIR/qt6ct/qt6ct.conf

	#echo "Done!"
else
	echo "Error..."
fi

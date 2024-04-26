#!/bin/env bash

function wal_notify(){
	dunstify -a "Color Palette" -u normal "$1"
}


wal_notify "Generating theme..."

# Generating theme using PyWal



wal_notify "Applying theme..."

# Applying theme (reloading)

# Hyprland

# Waybar
killall waybar
waybar &

wal_notify "Done!"
exit

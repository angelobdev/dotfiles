#!/bin/env bash

config_dir="$HOME/.config"
cache_dir="$HOME/.cache"

function wal_notify(){
	dunstify -a "Color Palette" -u normal "$1"
}

# Generating theme using PyWal
#wal_notify "Generating theme..."
wal -i "$config_dir/hypr/wallpapers/current.png"

# *** Applying theme ****
#wal_notify "Applying theme..."

# Reloading Hyprpaper
killall hyprpaper
hyprpaper &

# Hyprland
hyprctl reload

# Waybar
killall waybar
waybar &

# Alacritty
echo "#DO NOT EDIT THIS FILE, EDIT THE .base ONE INSTEAD!!!" > "$config_dir/alacritty/alacritty.toml"
cat "$config_dir/alacritty/alacritty.toml.base" >> "$config_dir/alacritty/alacritty.toml"
cat "$cache_dir/wal/colors-alacritty.toml" >> "$config_dir/alacritty/alacritty.toml"

# *** DONE ***
#wal_notify "Done!"
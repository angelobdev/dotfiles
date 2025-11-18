#!/bin/bash

mkdir -p ~/.local/share/hyprlock

hyprshot -o ~/.local/share/hyprlock -f lock.png -m output -m active -s

convert ~/.local/share/hyprlock/lock.png -blur 0x8 ~/.local/share/hyprlock/lock.png

hyprlock
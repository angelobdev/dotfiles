#!/bin/bash

# Getting current wallpaper
hyprpaperConfig="$HOME/.config/hypr/hyprpaper.conf"
current=$(cat "$hyprpaperConfig" | grep preload | cut -d '=' -f2 | sed 's/ //')

# Asking for new wallpaper
file=`zenity --title 'Select a new Wallpaper' --file-selection --file-filter="Images (PNG, JPEG) | *.png *.jpeg *.jpg"`

case $? in
       0)
              # Trying to change wallpaper
              ext=$(echo "$file" | cut -d '.' -f2)

              if [[ "$ext" == "png" ]]; then

			statusPreload=$(hyprctl hyprpaper preload "$file")
			statusWallpaper=$(hyprctl hyprpaper wallpaper ",$file")

                     if [[ "$statusPreload" == "ok" && "$statusWallpaper" == "ok" ]]; then
                            notify-send "Wallpaper changed!"
                            sed -i "s|$current|$file|" "$hyprpaperConfig"
                     else
                            notify-send "Something went wrong!"
                     fi

              else
                    notify-send "Please select an image file!"
              fi
              ;;
       1)
              notify-send "No file selected!";;
       -1)
              notify-send "An unexpected error has occurred!";;
esac

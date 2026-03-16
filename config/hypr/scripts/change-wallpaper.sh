#!/usr/bin/env bash

# Notify function
function notify(){
       notify-send --app-name "Hyprpaper" "$1"
}

# Getting current wallpaper
hyprpaperConfig="$HOME/.config/hypr/hyprpaper.conf"
current=$(cat "$hyprpaperConfig" | grep path | cut -d '=' -f2 | sed 's/ //')

# Asking for new wallpaper
file=`zenity --title 'Select a new Wallpaper' --file-selection --file-filter="Images (PNG, JPEG) | *.png *.jpeg *.jpg"`

case $? in
       0)
              # Trying to change wallpaper
              ext=$(echo "$file" | cut -d '.' -f2)

              if [[ "$ext" == "png" ]]; then

			statusWallpaper=$(hyprctl hyprpaper wallpaper ",$file")

                     if [[ "$statusWallpaper" == "" ]]; then
                            notify "Wallpaper changed!"
                            sed -i "s|$current|$file|" "$hyprpaperConfig"
                     else
                            notify "Something went wrong!"
                     fi

              else
                    notify "Please select an image file!"
              fi
              ;;
       1)
              notify "No file selected!";;
       -1)
              notify "An unexpected error has occurred!";;
esac
#!/bin/bash

CONFIG_FOLDER="$HOME/.config"

folders=(
    alacritty
    dunst
    hypr
    nwg-look
    qt5ct
    qt6ct
    waybar
    wlogout
    wofi
)

files=(
    chrome-flags.conf
    chromium-flags.conf
    electron-flags.conf
    electron13-flags.conf
    electron25-flags.conf
)

if [[ "$1" = "--save" ]]; then
    
    echo "Saving..."

    for folder in ${folders[@]}; do
        printf "$folder..."
        cp -R $CONFIG_FOLDER/$folder/* .config/$folder
        printf "Done!\n"
    done

    for file in ${files[@]}; do
        printf "$file..."
        cp $CONFIG_FOLDER/$file .config/
        printf "Done!\n"
    done

elif [[ "$1" = "--load" ]]; then
    
    echo "Loading..."
    cp -R .config/* $CONFIG_FOLDER
    echo "Done"

else

    echo "Please specify an option!"

fi
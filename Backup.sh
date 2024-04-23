#!/bin/bash

# Configuration files
CONFIG_DIR=".config"

config_dirs=(
    alacritty
    dunst
    gtk-3\.0
    hypr
    waybar
    wireplumber
    wlogout
    wofi
    xsettingsd
)

config_files=(
    chrome-flags.conf
    chromium-flags.conf
    electron-flags.conf
    electron13-flags.conf
    electron25-flags.conf
)

# Local files
LOCAL_DIR=".local"

if [[ "$1" = "--save" ]]; then
    
    echo "Saving..."

    # Config dirs
    for dir in ${config_dirs[@]}; do
        printf "$dir..."

        mkdir -p $CONFIG_DIR/$dir/
        cp -R $HOME/$CONFIG_DIR/$dir/* $CONFIG_DIR/$dir/
        
        printf "Done!\n"
    done

    # Config files
    for file in ${config_files[@]}; do
        printf "$file..."

        cp $HOME/$CONFIG_DIR/$file $CONFIG_DIR/
        
        printf "Done!\n"
    done

elif [[ "$1" = "--load" ]]; then
    
    echo "Loading..."
    cp -R $CONFIG_DIR/* $HOME/$CONFIG_DIR
    echo "Done"

else

    echo "Please specify an option!"

fi
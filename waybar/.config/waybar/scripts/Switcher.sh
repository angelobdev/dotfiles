#!/bin/bash

#################################################################################
#                                                                               #
#   This script has been written by angelobdev                                  #
#   It should be used in a properly configured Hyprland environment.            #
#                                                                               #
#   Look at the full configuration here: https://github.com/angelobdev/dotfiles #
#                                                                               #
#   The project (as well as this scripts) goes under the GNU GPLv3 LICENSE.     #
#                                                                               #
#################################################################################

# *** Parsing sinks ***
sinks=$(wpctl status)

# Getting sinks lines
sinks=$(sed -n "/Sinks/, /Sources/ { /Sinks/! { /Sources/! p } }" <<< "$sinks")

# Removing ASCII tree chars
sinks=$(sed -E "s/[├─└│]+//" <<< "$sinks")

# Removing spaces
sinks=$(awk '{$1=$1};1' <<< "$sinks")

# Removing volume
sinks=$(sed -E "s/\[vol: ([0-1]\.[0-9]{2})\]//" <<< "$sinks")

# Creating dictionary
declare -A sinks_dict
while IFS= read line; do

    # Getting sink device
    device=$(cut -d '.' -f2 <<< "$line")
    device="${device:1}" # (Removing first space)

    # Getting sink ID
    id=$(cut -d '.' -f1 <<< "$line")

    # Checking if current default
    if [[ "${id:0:1}" == '*' ]]; then
        device="<b>🟢 $device</b>"
        id=${id:2} # Removing * char
    else
        device="<b>🔴 $device</b>"
    fi

    # Adding sink to dictionary
    sinks_dict["$device"]="$id"
    
done <<< "$sinks"

# Getting sorted wofi output...
output=$(
    for device in "${!sinks_dict[@]}"; do
        echo "${sinks_dict[$device]}:$device"
    done | sort -n | cut -d ':' -f2
)

# ... and its number of lines
n_lines=$(wc -l <<< "$output")

# Creating wofi choice menu
killall wofi 2> /dev/null
choice=$(echo "$output" | wofi \
                            --show=dmenu \
                            --hide-scroll \
                            --allow-markup \
                            --sort-order=default \
                            --location=top_right \
                            --width=30% \
                            --lines=$((n_lines+2)) \
                            --xoffset=-30 \
                            --yoffset=10 \
                            --prompt="Choose the device..." \
                            /
)

# Setting default sink
if [[ $choice ]]; then
    sink_id="${sinks_dict[$choice]}"
    echo "Setting output to $choice with ID: $sink_id"
    wpctl set-default $sink_id
fi

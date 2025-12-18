#!/bin/bash
#################################################################################
#                                                                               #
#   This script has been written by angelobdev                                  #
#   Optimized for better performance and maintainability                        #
#                                                                               #
#   Look at the full configuration here: https://github.com/angelobdev/dotfiles #
#                                                                               #
#   The project (as well as this scripts) goes under the GNU GPLv3 LICENSE.     #
#                                                                               #
#################################################################################

# Kill any existing wofi instances early
pkill -x wofi 2>/dev/null

# Parse sinks in a single pass with awk
parse_sinks() {
    wpctl status | awk '
        /Sinks:/ { in_sinks=1; next }
        /Sources:/ { in_sinks=0 }
        in_sinks && /^[[:space:]]*[*│├└─]/ {
            # Remove tree characters and leading/trailing spaces
            gsub(/^[[:space:]]*[│├└─]+[[:space:]]*/, "")
            gsub(/[[:space:]]*\[vol:.*\]/, "")
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")
            
            # Extract ID and device name
            if (match($0, /^(\*?[[:space:]]*)?([0-9]+)\.[[:space:]]*(.+)/, arr)) {
                is_default = (arr[1] ~ /\*/)
                id = arr[2]
                device = arr[3]
                
                # Format output with indicator
                indicator = is_default ? "🟢" : "🔴"
                printf "%s:%s:<b>%s %s</b>\n", id, is_default, indicator, device
            }
        }
    '
}

# Get parsed sinks
mapfile -t sinks_array < <(parse_sinks)

# Check if we have any sinks
if [[ ${#sinks_array[@]} -eq 0 ]]; then
    notify-send "Audio Switch" "No audio sinks found" -u normal
    exit 1
fi

# Prepare wofi menu entries and build lookup table
declare -A sink_lookup
wofi_entries=""

for entry in "${sinks_array[@]}"; do
    IFS=':' read -r id is_default display <<< "$entry"
    sink_lookup["$display"]="$id"
    wofi_entries+="$display"$'\n'
done

# Remove trailing newline
wofi_entries="${wofi_entries%$'\n'}"

# Show wofi menu with modern styling
choice=$(echo "$wofi_entries" | wofi \
    --show=dmenu \
    --hide-scroll \
    --allow-markup \
    --sort-order=default \
    --location=top_right \
    --width=600 \
    --height=$((${#sinks_array[@]} * 40 + 80)) \
    --xoffset=-4 \
    --yoffset=4 \
    --prompt="Choose audio device" \
    --cache-file=/dev/null \
    --style="${XDG_CONFIG_HOME:-$HOME/.config}/wofi/style.css"
)

# Set default sink if selection was made
if [[ -n "$choice" ]]; then
    sink_id="${sink_lookup[$choice]}"
    if [[ -n "$sink_id" ]]; then
        wpctl set-default "$sink_id"
        # Extract device name without markup for notification
        device_name=$(echo "$choice" | sed 's/<[^>]*>//g' | sed 's/^[🟢🔴] //')
        notify-send "Audio Switch" "Switched to: $device_name" -u low -t 2000
    fi
fi
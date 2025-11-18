#!/bin/bash
#################################################################################
#                                                                               #
#   Volume control script with proper icon detection                           #
#   Optimized for modern notification system                                   #
#                                                                               #
#################################################################################

# Try to detect icon theme and path
detect_icon_path() {
    local possible_paths=(
        "$HOME/.local/share/icons"
        "/usr/share/icons"
        "/usr/local/share/icons"
    )
    
    # Get current icon theme from gsettings or use fallback
    local icon_theme
    if command -v gsettings &>/dev/null; then
        icon_theme=$(gsettings get org.gnome.desktop.interface icon-theme 2>/dev/null | tr -d "'")
    fi
    
    # Fallback themes to try
    local themes=("${icon_theme}" "Papirus-Dark" "Papirus" "Adwaita" "hicolor")
    
    for theme in "${themes[@]}"; do
        [[ -z "$theme" ]] && continue
        for base_path in "${possible_paths[@]}"; do
            local test_path="${base_path}/${theme}/24x24/actions"
            if [[ -d "$test_path" ]]; then
                echo "$test_path"
                return 0
            fi
            # Try symbolic variant
            test_path="${base_path}/${theme}/symbolic/actions"
            if [[ -d "$test_path" ]]; then
                echo "$test_path"
                return 0
            fi
        done
    done
    
    # Ultimate fallback - just use notification daemon's default
    echo ""
}

icon_path=$(detect_icon_path)

# Get volume icon based on current level
get_volume_icon() {
    local volume=$1
    local muted=$2
    local icon_name
    
    if [[ "$muted" == "MUTED" ]] || [[ $volume -eq 0 ]]; then
        icon_name="audio-volume-muted"
    elif [[ $volume -le 33 ]]; then
        icon_name="audio-volume-low"
    elif [[ $volume -le 66 ]]; then
        icon_name="audio-volume-medium"
    else
        icon_name="audio-volume-high"
    fi
    
    # Try to find the icon file
    if [[ -n "$icon_path" ]]; then
        for ext in svg png; do
            if [[ -f "${icon_path}/${icon_name}.${ext}" ]]; then
                echo "${icon_path}/${icon_name}.${ext}"
                return 0
            fi
        done
    fi
    
    # Fallback to icon name only (let notification daemon handle it)
    echo "$icon_name"
}

# Get current volume info
get_volume_info() {
    local output
    output=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
    
    local wpvol=$(echo "$output" | awk '{print $2}')
    local muted=$(echo "$output" | grep -o "MUTED")
    local volume=$(awk "BEGIN {printf \"%.0f\", $wpvol * 100}")
    
    echo "$volume|$muted"
}

# Send volume notification
vol_notify() {
    local info=$(get_volume_info)
    local current_volume=$(echo "$info" | cut -d'|' -f1)
    local muted=$(echo "$info" | cut -d'|' -f2)
    
    local icon=$(get_volume_icon "$current_volume" "$muted")
    
    local notify_args=(
        -h "int:value:$current_volume"
        -h "string:synchronous:volume"
        -h "int:icon-size:32"
        -c "progress"
        -a "Volume"
    )
    
    # Add icon if found
    if [[ -f "$icon" ]]; then
        notify_args+=(-h "string:image-path:$icon")
    else
        notify_args+=(-i "$icon")
    fi
    
    if [[ "$muted" == "MUTED" ]]; then
        notify-send "${notify_args[@]}" "Muted"
    else
        notify-send "${notify_args[@]}" "Volume: ${current_volume}%"
    fi
}

# Volume up
up() {
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+ -l 1.0
    vol_notify
}

# Volume down
down() {
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- -l 1.0
    vol_notify
}

# Toggle mute
mute() {
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
    vol_notify
}

# Microphone mute toggle
mic_mute() {
    wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
    local muted=$(wpctl get-volume @DEFAULT_AUDIO_SOURCE@ | grep -o "MUTED")
    
    local icon
    if [[ "$muted" == "MUTED" ]]; then
        icon=$(get_volume_icon 0 "MUTED")
        if [[ -f "$icon" ]]; then
            notify-send -h "string:image-path:$icon" -a "Microphone" "Mic Muted"
        else
            notify-send -i "$icon" -a "Microphone" "Mic Muted"
        fi
    else
        icon="audio-input-microphone"
        if [[ -n "$icon_path" ]] && [[ -f "${icon_path}/${icon}.svg" ]]; then
            notify-send -h "string:image-path:${icon_path}/${icon}.svg" -a "Microphone" "Mic Unmuted"
        else
            notify-send -i "$icon" -a "Microphone" "Mic Unmuted"
        fi
    fi
}

# Main command handler
case "$1" in
    "--up"|"-u"|"up")
        up
        ;;
    "--down"|"-d"|"down")
        down
        ;;
    "--mute"|"-m"|"mute")
        mute
        ;;
    "--mic-mute"|"--mic"|"mic")
        mic_mute
        ;;
    *)
        echo "Usage: $0 {--up|--down|--mute|--mic-mute}"
        echo "  --up, -u, up          Increase volume by 5%"
        echo "  --down, -d, down      Decrease volume by 5%"
        echo "  --mute, -m, mute      Toggle mute"
        echo "  --mic-mute, --mic     Toggle microphone mute"
        exit 1
        ;;
esac
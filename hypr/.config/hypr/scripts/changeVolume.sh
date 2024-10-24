#!/bin/bash

vol_notify(){
    current_volume=$(echo$(($(wpctl get-volume @DEFAULT_AUDIO_SINK@ | cut -d ' ' -f2) * 100)) | sed 's/\.//')
    notify-send "Volume: $current_volume%"
    # notify-send -h int:value:$(${current_volume}) "Ciao"
}

up(){
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+ -l 1
    vol_notify
}

down(){
    wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%- -l 1
    vol_notify
}

mute(){
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
    muted=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep "MUTED")

    if [[ "$muted" ]]; then
        notify-send -a "Wireplumber" "Sink muted"
    else
        notify-send -a "Wireplumber" "Sink unmuted"
    fi
}

mic_mute(){
    wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
    muted=$(wpctl get-volume @DEFAULT_AUDIO_SOURCE@ | grep "MUTED")

    if [[ "$muted" ]]; then
        notify-send -a "Wireplumber" "Mic muted"
    else
        notify-send -a "Wireplumber" "Mic unmuted"
    fi
}

case "$1" in
"--up")
    up;;

"--down")
    down;;

"--mute")
    mute;;

"--mic-mute")
    mic_mute;;
        
esac
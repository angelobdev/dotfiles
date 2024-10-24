#!/bin/bash

vol_notify(){
    wpvol=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | cut -d ' ' -f2)
    current_volume=$(bc -l <<< "$wpvol * 100" | cut -d '.' -f1)

    icon_name="audio-volume-high"
    # if [[ $current_volume == 0]]; then
    #     icon_name="audio-volume-muted"
    # elif [[ $current_volume > 0 ]]; then
    #     icon_name="audio-volume-low"
    # elif [[ $current_volume > 40]]; then
    #     icon_name="audio-volume-medium"
    # elif [[ $current_volume > 80]]; then
    #     icon_name="audio-volume-high"
    # fi

    notify-send " " -h int:value:$current_volume -h string:synchronous:volume -c progress -i "$icon_name" -a "Volume"
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
#/bin/bash

delta=$1

if (( $delta > 0 )); then
	wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ $delta%+;
elif (( $delta < 0 )); then
	wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ ${delta#-}%-;
else
	wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
	exit
fi

volume=$(wpctl get-volume @DEFAULT_SINK@ | cut -d ' ' -f2)
volume=$(bc -l <<< "$volume * 100")

notify-send -h int:value:"$volume" -a "Volume" -c progress "."

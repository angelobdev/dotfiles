#!/bin/bash

device_id=$1
delta=$2

# Getting device ID
case $device_id in
	D)
		device=gmux_backlight
		device_name=Display
		;;
	K)
		device=apple::kbd_backlight
		device_name=Keyboard
		;;
	*)
		notify-send -u critical -a "Brightness Control" "Invalid device"
		exit;
		;;
esac

# Checking if brigthness is going up or down
if (( $delta < 0 )); then
	brightnessctl -d "$device" set ${delta#-}%- -q
else
	brightnessctl -d "$device" set $delta%+ -q
fi

max=$(brightnessctl -d "$device" m);
current=$(brightnessctl -d "$device" g);
perc=$(bc <<< "scale=2; $current/$max*100")

notify-send -h int:value:"$perc" -a "$device_name Backlight" -c progress "."

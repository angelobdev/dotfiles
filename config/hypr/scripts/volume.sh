#!/bin/bash

case "$1" in
    "--up"|"-u"|"up")
        swayosd-client --output-volume raise
        ;;
    "--down"|"-d"|"down")
        swayosd-client --output-volume lower
        ;;
    "--mute"|"-m"|"mute")
        swayosd-client --output-volume mute-toggle
        ;;
    "--mic-mute"|"--mic"|"mic")
        swayosd-client --input-volume mute-toggle
        ;;
    *)
        echo "Usage: $0 {--up|--down|--mute|--mic-mute}"
        exit 1
        ;;
esac
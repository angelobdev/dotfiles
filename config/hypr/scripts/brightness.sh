#!/bin/bash

case "$1" in
    "--up"|"-u"|"up")
        swayosd-client --brightness raise
        ;;
    "--down"|"-d"|"down")
        swayosd-client --brightness lower
        ;;
    "--set"|"-s"|"set")
        if [[ -z "$2" ]]; then
            echo "Error: Please provide brightness level (0-100)"
            exit 1
        fi
        brightnessctl set "$2%"
        # SwayOSD will auto-detect the change
        ;;
    *)
        echo "Usage: $0 {--up|--down|--set <level>}"
        exit 1
        ;;
esac
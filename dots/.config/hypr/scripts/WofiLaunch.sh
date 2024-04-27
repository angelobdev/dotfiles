#!/bin/bash

killall wofi
wofi --show drun --allow-images -a -i --prompt "Search..." --color "$HOME/.cache/wal/colors"

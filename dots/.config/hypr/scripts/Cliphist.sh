#!/bin/bash

cliphist | wofi --dmenu | cliphist decode | wl-copy

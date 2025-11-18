#!/bin/bash

option="$1"

askConfirm(){
    zenity --question --title="Hyprland" --text="$1"
    return $?
}

    case "$option" in
        "poweroff")
            if askConfirm "Do you want to shut the computer down?"; then
                systemctl poweroff
            fi
        ;;
        "reboot")
            if askConfirm "Do you want to reboot the system?"; then
                systemctl reboot
            fi
        ;;
        "sleep")
            if askConfirm "Do you want to suspend?"; then
                systemctl suspend
            fi
        ;;
        "logout")
            if askConfirm "Do you want to log out?"; then
                hyprctl dispatch exit 0
            fi
        ;;
        "lock")
            if askConfirm "Do you want to lock?"; then
                hyprlock
            fi
        ;;
    esac


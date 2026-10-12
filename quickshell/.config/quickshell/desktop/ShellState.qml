pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

Singleton {
    id: root
    property string panel: ""
    property var activeScreen: null
    function toggle(name, screen) {
        if (!["launcher", "controls", "network", "bluetooth", "audio", "battery", "notifications", "calendar", "hints", "wallpaper", "clipboard", "recording", "power"].includes(name))
            return;
        activeScreen = screen || Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) || Quickshell.screens[0];
        panel = panel === name ? "" : name;
    }
    function close() {
        panel = "";
    }
}

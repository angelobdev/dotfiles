pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

Singleton {
    id: root
    property string panel: ""
    property var activeScreen: null
    // Direction of the last move between the Control Center and a sub-panel: 1 forward, -1 back, 0 none.
    property int navigation: 0
    function toggle(name, screen) {
        show(name, screen, 0);
    }
    // Opens a Control Center sub-panel; panels slide sideways instead of dropping from the bar.
    function push(name) {
        show(name, activeScreen, 1);
    }
    function back() {
        show("controls", activeScreen, -1);
    }
    function show(name, screen, direction) {
        if (!["launcher", "controls", "network", "bluetooth", "audio", "battery", "notifications", "calendar", "hints", "wallpaper", "theming", "clipboard", "recording", "power"].includes(name))
            return;
        // Set before the panel changes so both the closing and the opening panel read the same direction.
        navigation = direction;
        activeScreen = screen || screenNamed(Hyprland.focusedMonitor?.name);
        panel = panel === name ? "" : name;
    }
    function screenNamed(name) {
        return Quickshell.screens.find(s => s.name === name) || Quickshell.screens[0];
    }
    function close() {
        navigation = 0;
        panel = "";
    }
}

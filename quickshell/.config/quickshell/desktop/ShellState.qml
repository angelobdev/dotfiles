pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

Singleton {
    id: root
    property string panel: ""
    // Opens the window menu of the bar on that monitor (assist button, IPC).
    signal windowMenuRequested(string screenName)
    function requestWindowMenu() {
        windowMenuRequested(Hyprland.focusedMonitor?.name ?? "");
    }
    property var activeScreen: null
    // What panels keep between openings while they are unloaded (components/LazyPanel.qml): expanded sections,
    // tabs, folders. Read once when a panel is created, written as it changes; gone with the shell.
    property var memory: ({})
    function recall(key, fallback) {
        return key in memory ? memory[key] : fallback;
    }
    function remember(key, value) {
        memory[key] = value;
    }
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
        if (!["launcher", "controls", "network", "bluetooth", "audio", "battery", "notifications", "calendar", "hints", "wallpaper", "theming", "clipboard", "recording", "power", "agent", "updates", "emoji", "displays"].includes(name))
            return;
        // Set before the panel changes so both the closing and the opening panel read the same direction.
        navigation = direction ?? 0;
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
    // A panel on a monitor that went away closes; the next one opens on the focused monitor.
    Connections {
        target: Quickshell
        function onScreensChanged() {
            if (root.activeScreen && !Quickshell.screens.includes(root.activeScreen)) {
                root.close();
                root.activeScreen = null;
            }
        }
    }
}

pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland

Singleton {
    id: root
    property string panel: ""
    // Opens the window menu of the bar on that monitor (assist button, IPC).
    signal windowMenuRequested(string screenName)
    // Opens the desktop menu in the middle of that monitor (IPC; the desktop itself opens it at the pointer).
    signal desktopMenuRequested(string screenName)
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
    // Every panel: shell.qml has a LazyPanel for each and desktop-shell toggle accepts the same names
    // (scripts/tests/test_panels.py keeps the three in step).
    readonly property var panels: ["launcher", "controls", "network", "bluetooth", "audio", "battery", "notifications", "calendar", "hints", "wallpaper", "settings", "clipboard", "recording", "power", "agent", "updates", "emoji", "displays"]
    // Former panels that are now a section of another: their names keep working (shortcuts, desktop-shell
    // toggle, assist actions) and open that section.
    readonly property var aliases: ({
            theming: {
                panel: "settings",
                section: "appearance"
            }
        })
    // A panel already open is asked to move to another of its sections (panels/SettingsPanel.qml).
    signal sectionRequested(string name, string section)
    function show(name, screen, direction) {
        const alias = aliases[name];
        if (alias) {
            openSection(alias.panel, alias.section, screen, true);
            return;
        }
        if (!panels.includes(name))
            return;
        // Set before the panel changes so both the closing and the opening panel read the same direction.
        navigation = direction ?? 0;
        activeScreen = screen || screenNamed(Hyprland.focusedMonitor?.name);
        panel = panel === name ? "" : name;
    }
    // Opens a panel on one of its sections, or moves it there when it is open on another. With toggle, asking
    // again for the section on screen closes it, as toggle() does for a panel.
    function openSection(name, section, screen, toggle) {
        if (!panels.includes(name))
            return;
        if (panel === name && recall(name + "/section", "") === section) {
            if (toggle)
                close();
            return;
        }
        remember(name + "/section", section);
        if (panel === name) {
            sectionRequested(name, section);
            return;
        }
        navigation = 0;
        activeScreen = screen || screenNamed(Hyprland.focusedMonitor?.name);
        panel = name;
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

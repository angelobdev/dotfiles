import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import "../services"

// The drop-down assistant console closes on a click or tap outside it. While it is open on this screen,
// this transparent layer under every window takes those presses: the special workspace keeps them from
// the windows below it (input.special_fallthrough is off), so nothing else gets them.
// When the console closes it also takes the keyboard from the console window: Hyprland leaves the focus on it,
// hidden, when there is no window on the workspace below, so the keys would still go to the console and the next
// reload would show it again. The layer holds the keyboard for a moment and lets it go: then no window has it,
// or the one Hyprland gives it back to below.
PanelWindow {
    id: root
    // From the screen model (reading screen.name here loops: mapping the window updates it).
    required property string screenName
    readonly property bool open: screenName !== "" && Agent.consoleScreen === screenName
    property bool releasing: false
    visible: open || releasing
    onOpenChanged: {
        const active = Hyprland.activeToplevel;
        const app = active?.wayland?.appId || active?.lastIpcObject?.class || "";
        if (!open && (app === "herdr-app" || app === "desktop-ai")) {
            releasing = true;
            release.restart();
        }
    }
    Timer {
        id: release
        interval: 150
        onTriggered: root.releasing = false
    }
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Bottom
    WlrLayershell.namespace: "desktop-console-catcher"
    WlrLayershell.keyboardFocus: releasing ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    MouseArea {
        anchors.fill: parent
        enabled: root.open
        acceptedButtons: Qt.AllButtons
        onPressed: Agent.hideConsole(root.screenName)
    }
}

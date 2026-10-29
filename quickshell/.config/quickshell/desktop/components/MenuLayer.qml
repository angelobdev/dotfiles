import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland

// The full-screen layer of a menu (tray, window, dock), so the menu can extend beyond the bar or the dock,
// grab the keyboard and close on any outside press: dismissRequested comes from a press outside the menu
// or from another window taking the focus. The menu is placed with clampX and clampY.
PanelWindow {
    id: root
    signal dismissRequested
    // The position of a menu of the given size, kept 6 px inside the screen.
    function clampX(x, size) {
        return Math.max(6, Math.min(x, width - size - 6));
    }
    function clampY(y, size) {
        return Math.max(6, Math.min(y, height - size - 6));
    }
    visible: false
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-tray-menu"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    HyprlandFocusGrab {
        active: root.visible
        windows: [root]
        onCleared: root.dismissRequested()
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onPressed: root.dismissRequested()
    }
}

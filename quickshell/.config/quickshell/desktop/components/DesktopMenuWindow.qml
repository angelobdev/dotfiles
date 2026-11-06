import QtQuick
import Quickshell
import ".."
import "../services"

// The desktop menu of one screen, from a right click or long press on the empty desktop (DesktopCatcher):
// the launcher, Settings, and the session menu (lock, suspend, log out, restart, shut down, with its own
// confirmations).
MenuLayer {
    id: root
    property point origin: Qt.point(0, 0)
    // Opened from the IPC: in the middle of the screen, once the layer has its size.
    property bool centered: false
    onDismissRequested: dismiss()
    function popup(x, y, middle) {
        origin = Qt.point(x, y);
        centered = middle === true;
        visible = true;
        Qt.callLater(() => menu.forceActiveFocus());
    }
    function dismiss() {
        visible = false;
    }
    Connections {
        target: ShellState
        function onDesktopMenuRequested(screenName) {
            if (screenName === root.screen?.name)
                root.popup(0, 0, true);
        }
    }
    // A panel on this screen; Settings on the section seen last.
    function open(name) {
        if (name === "settings")
            ShellState.openSection("settings", ShellState.recall("settings/section", "appearance"), screen, false);
        else
            ShellState.toggle(name, screen);
    }
    PopupMenu {
        id: menu
        x: root.centered ? (root.width - width) / 2 : root.clampX(root.origin.x, width)
        y: root.centered ? (root.height - height) / 2 : root.clampY(root.origin.y, height)
        entries: [
            {
                text: I18n.tr("desktopMenu.launcher"),
                action: () => root.open("launcher")
            },
            {
                text: I18n.tr("desktopMenu.settings"),
                action: () => root.open("settings")
            },
            {
                kind: "separator"
            },
            {
                text: I18n.tr("desktopMenu.session"),
                action: () => root.open("power")
            }
        ]
        onTriggered: root.dismiss()
        onDismissed: root.dismiss()
    }
}

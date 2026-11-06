import QtQuick
import Quickshell
import ".."
import "../services"

// The desktop menu of one screen, from a right click or long press on the empty desktop (DesktopCatcher):
// the launcher and Settings, then the session: Lock at once, and the others through the session menu,
// opened on their confirmation.
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
    // A session action: lock at once; the rest ask in the session menu first, as there.
    function session(action) {
        if (action === "lock") {
            Quickshell.execDetached([Quickshell.env("HOME") + "/.local/bin/desktop-power", "lock"]);
            return;
        }
        ShellState.remember("power/ask", action);
        ShellState.toggle("power", screen);
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
                kind: "heading",
                text: I18n.tr("desktopMenu.open")
            },
            {
                text: I18n.tr("desktopMenu.launcher"),
                glyph: "apps",
                action: () => root.open("launcher")
            },
            {
                text: I18n.tr("desktopMenu.settings"),
                glyph: "controls",
                action: () => root.open("settings")
            },
            {
                kind: "separator"
            },
            {
                kind: "heading",
                text: I18n.tr("desktopMenu.session")
            },
            {
                text: I18n.tr("session.lock"),
                glyph: "lock",
                action: () => root.session("lock")
            },
            {
                text: I18n.tr("desktopMenu.suspend"),
                glyph: "suspend",
                action: () => root.session("suspend")
            },
            {
                text: I18n.tr("desktopMenu.logout"),
                glyph: "logout",
                destructive: true,
                action: () => root.session("logout")
            },
            {
                text: I18n.tr("desktopMenu.reboot"),
                glyph: "reboot",
                destructive: true,
                action: () => root.session("reboot")
            },
            {
                text: I18n.tr("desktopMenu.powerOff"),
                glyph: "power",
                destructive: true,
                action: () => root.session("poweroff")
            }
        ]
        onTriggered: root.dismiss()
        onDismissed: root.dismiss()
    }
}

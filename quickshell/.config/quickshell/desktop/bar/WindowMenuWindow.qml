import QtQuick
import Quickshell
import Quickshell.Hyprland
import ".."
import "../components"

// Actions on the active window, from a long press or right click on its title in the bar (or on the app
// button that replaces the title on a narrow bar): touch has no Super+Q, Super+Shift+F or Super+V.
MenuLayer {
    id: root
    property point origin: Qt.point(0, 0)
    onDismissRequested: dismiss()
    function popup(item, x, y) {
        if (!Hyprland.activeToplevel)
            return;
        // lastIpcObject (floating) is only filled by a refresh; the entries follow when it arrives.
        Hyprland.refreshToplevels();
        origin = item.mapToItem(item.QsWindow.window.contentItem, x, y);
        visible = true;
        Qt.callLater(() => menu.forceActiveFocus());
    }
    function dismiss() {
        visible = false;
    }
    function dispatch(command) {
        Hyprland.dispatch(command);
    }
    function entries() {
        const window = Hyprland.activeToplevel;
        if (!window)
            return [];
        return [
            {
                kind: "heading",
                text: window.title || window.wayland?.appId || ""
            },
            {
                text: I18n.tr("windowMenu.fullscreen"),
                action: () => root.dispatch("hl.dsp.window.fullscreen()")
            },
            {
                text: I18n.tr("windowMenu.floating"),
                checked: window.lastIpcObject?.floating === true,
                action: () => root.dispatch("hl.dsp.window.float({ action = \"toggle\" })")
            },
            {
                text: I18n.tr("windowMenu.movePrevious"),
                action: () => root.dispatch("hl.dsp.window.move({ workspace = \"r-1\" })")
            },
            {
                text: I18n.tr("windowMenu.moveNext"),
                action: () => root.dispatch("hl.dsp.window.move({ workspace = \"r+1\" })")
            },
            {
                kind: "separator"
            },
            {
                text: I18n.tr("windowMenu.close"),
                destructive: true,
                action: () => window.wayland?.close()
            }
        ];
    }
    PopupMenu {
        id: menu
        x: root.clampX(root.origin.x, width)
        y: root.clampY(root.origin.y, height)
        entries: root.visible ? root.entries() : []
        onTriggered: root.dismiss()
        onDismissed: root.dismiss()
    }
}

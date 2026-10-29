import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import ".."
import "../components"

// Actions on the active window, from a long press or right click on its title in the bar (or on the app
// button that replaces the title on a narrow bar): touch has no Super+Q, Super+Shift+F or Super+V.
PanelWindow {
    id: root
    property point origin: Qt.point(0, 0)
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
    function popup(item, x, y) {
        if (!Hyprland.activeToplevel)
            return;
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
    HyprlandFocusGrab {
        active: root.visible
        windows: [root]
        onCleared: root.dismiss()
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onPressed: root.dismiss()
    }
    PopupMenu {
        id: menu
        x: Math.max(6, Math.min(root.origin.x, root.width - width - 6))
        y: Math.max(6, Math.min(root.origin.y, root.height - height - 6))
        entries: root.visible ? root.entries() : []
        onTriggered: root.dismiss()
        onDismissed: root.dismiss()
    }
}

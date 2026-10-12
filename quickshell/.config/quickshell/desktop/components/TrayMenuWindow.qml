import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

// QML menus live in a layer surface so cascades can extend beyond the 38 px bar.
PanelWindow {
    id: root
    property var menuEntry: null
    readonly property alias menu: menu
    visible: false
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-tray-menu"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    function popup(item, x, y) {
        if (!menuEntry) return;
        const origin = item.mapToItem(item.QsWindow.window.contentItem, x, y);
        visible = true;
        Qt.callLater(() => {
            menu.popup(Math.max(6, Math.min(origin.x, width - menu.implicitWidth - 6)), origin.y);
        });
    }
    function dismiss() {
        menu.dismiss();
        visible = false;
    }
    onVisibleChanged: if (!visible) menu.dismiss()
    onMenuEntryChanged: if (!menuEntry) dismiss()
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
    TrayMenu {
        id: menu
        parent: root.contentItem
        menuEntry: root.menuEntry
        onClosed: root.visible = false
    }
}

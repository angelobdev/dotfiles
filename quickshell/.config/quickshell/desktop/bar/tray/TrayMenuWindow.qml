import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland

// QML menus live in a layer surface so cascades can extend beyond the 38 px bar.
PanelWindow {
    id: root
    property var menuEntry: null
    readonly property alias menu: menu
    property point menuOrigin: Qt.point(0, 0)
    visible: false
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-tray-menu"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    function popup(item, x, y) {
        if (!menuEntry) return;
        menuOrigin = item.mapToItem(item.QsWindow.window.contentItem, x, y);
        visible = true;
        Qt.callLater(() => {
            menu.popup();
            positionMenu();
        });
    }
    function positionMenu() {
        if (!menu.visible) return;
        menu.x = Math.max(6, Math.min(menuOrigin.x, width - menu.width - 6));
        menu.y = Math.max(6, Math.min(menuOrigin.y, height - menu.height - 6));
    }
    // Layer surfaces receive their monitor size after being mapped. Keep the
    // original icon position instead of retaining the clamp to the initial size.
    onWidthChanged: positionMenu()
    onHeightChanged: positionMenu()
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
        onOpened: root.positionMenu()
        onWidthChanged: root.positionMenu()
        onHeightChanged: root.positionMenu()
        onClosed: root.visible = false
    }
}

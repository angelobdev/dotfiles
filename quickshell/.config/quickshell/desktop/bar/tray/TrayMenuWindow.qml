import QtQuick
import Quickshell
import "../../components"

// QML menus live in a layer surface so cascades can extend beyond the 38 px bar.
MenuLayer {
    id: root
    property var menuEntry: null
    property point menuOrigin: Qt.point(0, 0)
    onDismissRequested: dismiss()
    function popup(item, x, y) {
        if (!menuEntry)
            return;
        menuOrigin = item.mapToItem(item.QsWindow.window.contentItem, x, y);
        visible = true;
        Qt.callLater(() => {
            menu.popup();
            positionMenu();
        });
    }
    function positionMenu() {
        if (!menu.visible)
            return;
        menu.x = clampX(menuOrigin.x, menu.width);
        menu.y = clampY(menuOrigin.y, menu.height);
    }
    // Layer surfaces receive their monitor size after being mapped. Keep the
    // original icon position instead of retaining the clamp to the initial size.
    onWidthChanged: positionMenu()
    onHeightChanged: positionMenu()
    function dismiss() {
        menu.dismiss();
        visible = false;
    }
    onVisibleChanged: if (!visible)
        menu.dismiss()
    onMenuEntryChanged: if (!menuEntry)
        dismiss()
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

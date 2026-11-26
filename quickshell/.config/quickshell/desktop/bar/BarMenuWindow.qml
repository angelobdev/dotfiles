import QtQuick
import Quickshell
import ".."
import "../components"

// A menu of the bar from PopupMenu entries: the bar menu (a right click on its empty part) and, while the bar
// is edited, the menu of a widget.
MenuLayer {
    id: root
    property point origin: Qt.point(0, 0)
    property var entries: []
    onDismissRequested: dismiss()
    function popup(item, x, y, entries) {
        root.entries = entries;
        origin = item.mapToItem(item.QsWindow.window.contentItem, x, y);
        visible = true;
        Qt.callLater(() => menu.forceActiveFocus());
    }
    function dismiss() {
        visible = false;
    }
    PopupMenu {
        id: menu
        x: root.clampX(root.origin.x, width)
        y: root.clampY(root.origin.y, height)
        entries: root.visible ? root.entries : []
        onTriggered: root.dismiss()
        onDismissed: root.dismiss()
    }
}

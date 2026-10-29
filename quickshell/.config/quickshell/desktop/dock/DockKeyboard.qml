import QtQuick
import Quickshell
import Quickshell.Wayland

// Holds the keyboard for a dock opened with Super+D, mapped only while it does, like tray menus.
// The dock window itself never takes focus: Qt replayed a stale hover on it, so the dock thought the
// pointer was over it and never hid. The surface covers the screen except the dock, so a click anywhere
// else ends keyboard mode while clicks on the dock still reach it.
PanelWindow {
    id: root
    // The dock body in this surface's coordinates (the dock is anchored to the bottom of the same screen).
    property rect hole: Qt.rect(0, 0, 0, 0)
    property bool active: false
    signal stepRequested(int direction)
    signal firstRequested
    signal lastRequested
    signal activateRequested(bool newInstance)
    signal menuRequested
    signal closeRequested
    signal outsideClicked
    visible: active
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-dock-keys"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    mask: Region {
        item: keys
        Region {
            x: root.hole.x
            y: root.hole.y
            width: root.hole.width
            height: root.hole.height
            intersection: Intersection.Subtract
        }
    }
    onVisibleChanged: if (visible)
        keys.forceActiveFocus()
    Item {
        id: keys
        anchors.fill: parent
        focus: true
        Keys.onLeftPressed: root.stepRequested(-1)
        Keys.onRightPressed: root.stepRequested(1)
        Keys.onTabPressed: root.stepRequested(1)
        Keys.onBacktabPressed: root.stepRequested(-1)
        Keys.onEscapePressed: root.closeRequested()
        Keys.onPressed: event => {
            if (event.key === Qt.Key_Home)
                root.firstRequested();
            else if (event.key === Qt.Key_End)
                root.lastRequested();
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter)
                root.activateRequested((event.modifiers & Qt.ShiftModifier) !== 0);
            else if (event.key === Qt.Key_Menu || event.key === Qt.Key_F10 && event.modifiers & Qt.ShiftModifier)
                root.menuRequested();
            else
                return;
            event.accepted = true;
        }
        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onPressed: root.outsideClicked()
        }
    }
}

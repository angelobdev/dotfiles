pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.SystemTray
import "../.."

// The status icons of apps (StatusNotifierItem).
RowLayout {
    id: root
    property var bar
    // Passive means nothing to show right now (udiskie with no removable device, for one).
    readonly property bool shown: SystemTray.items.values.some(item => item.status !== Status.Passive)
    spacing: 5
    Repeater {
        model: SystemTray.items
        Item {
            id: trayItem
            required property var modelData
            visible: modelData.status !== Status.Passive
            implicitWidth: Theme.hit(30)
            implicitHeight: Theme.hit(30)
            Accessible.role: Accessible.Button
            Accessible.name: modelData.tooltipTitle || modelData.title || modelData.id
            Image {
                anchors.centerIn: parent
                width: Theme.hit(16)
                height: Theme.hit(16)
                source: trayItem.modelData.icon
            }
            MouseArea {
                // A long press (touch) opens the menu like a right click; the release then does nothing.
                property bool held: false
                function openMenu() {
                    if (trayItem.modelData.hasMenu) {
                        root.bar.trayMenu.menuEntry = trayItem.modelData.menu;
                        root.bar.trayMenu.popup(trayItem, 0, trayItem.height + 8);
                    }
                }
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                pressAndHoldInterval: 500
                onPressed: held = false
                onPressAndHold: mouse => {
                    if (mouse.button !== Qt.LeftButton)
                        return;
                    held = true;
                    openMenu();
                }
                onClicked: mouse => {
                    if (held)
                        return;
                    if (mouse.button === Qt.MiddleButton)
                        trayItem.modelData.secondaryActivate();
                    else if (mouse.button === Qt.RightButton || trayItem.modelData.onlyMenu)
                        openMenu();
                    else
                        trayItem.modelData.activate();
                }
                onWheel: event => trayItem.modelData.scroll(event.angleDelta.y, false)
            }
        }
    }
}

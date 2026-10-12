import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Networking
import Quickshell.Services.SystemTray
import Quickshell.Services.UPower
import ".."
import "../components"
import "../services"
PanelWindow {
    id: bar
    anchors { top: true; left: true; right: true }
    implicitHeight: 48
    color: Theme.background
    WlrLayershell.namespace: "desktop-bar"
    readonly property var monitor: Hyprland.monitorFor(screen)
    SystemClock { id: clock; precision: SystemClock.Minutes }
    RowLayout {
        anchors { fill: parent; leftMargin: 12; rightMargin: 12 }
        spacing: 6
        ActionButton { text: "App"; highlighted: true; onClicked: ShellState.toggle("launcher", bar.screen) }
        Repeater {
            model: 10
            ActionButton {
                required property int index
                text: String(index + 1)
                implicitWidth: 30
                highlighted: bar.monitor?.activeWorkspace?.id === index + 1
                onClicked: Hyprland.dispatch("hl.dsp.focus({ workspace = " + (index + 1) + " })")
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.leftMargin: 10
            text: Hyprland.activeToplevel?.title ?? "Desktop"
            elide: Text.ElideRight
            textFormat: Text.PlainText
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
            visible: bar.width > 1100
        }
        Item { Layout.fillWidth: true; visible: bar.width <= 1100 }
        Repeater {
            model: SystemTray.items
            Item {
                id: trayItem
                required property var modelData
                implicitWidth: 28; implicitHeight: 32
                Image { anchors.centerIn: parent; width: 20; height: 20; source: trayItem.modelData.icon }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                    onClicked: mouse => {
                        if (mouse.button === Qt.MiddleButton) trayItem.modelData.secondaryActivate();
                        else if (mouse.button === Qt.RightButton || trayItem.modelData.onlyMenu) {
                            if (trayItem.modelData.hasMenu) {
                                const point = mapToItem(bar.contentItem, mouse.x, mouse.y);
                                trayItem.modelData.display(bar, point.x, point.y);
                            }
                        } else trayItem.modelData.activate();
                    }
                    onWheel: event => trayItem.modelData.scroll(event.angleDelta.y, false)
                }
            }
        }
        ActionButton {
            text: Audio.muted ? "Audio ×" : "Vol " + Audio.volume + "%"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton {
            visible: bar.width > 850
            text: Networking.devices.values.some(d => d.connected) ? "Rete ●" : "Rete ○"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton {
            visible: UPower.displayDevice?.isLaptopBattery ?? false
            text: "Bat " + Math.round((UPower.displayDevice?.percentage ?? 0) * 100) + "%"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton { text: "N " + Notices.notifications.values.length; onClicked: ShellState.toggle("notifications", bar.screen) }
        Text {
            text: Qt.formatDateTime(clock.date, "ddd d MMM  HH:mm")
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: 13
            Layout.leftMargin: 8; Layout.rightMargin: 8
        }
        ActionButton { text: "⏻"; onClicked: ShellState.toggle("power", bar.screen) }
    }
}

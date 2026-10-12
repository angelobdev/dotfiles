import QtQuick
import QtQuick.Controls
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
    margins { top: 8; left: 12; right: 12 }
    implicitHeight: 46
    color: "transparent"
    WlrLayershell.namespace: "desktop-bar"
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property var workspaces: Hyprland.workspaces.values.filter(w =>
        w.id > 0 && w.monitor?.name === bar.screen.name && (w.active || w.toplevels.values.length > 0)).sort((a, b) => a.id - b.id)
    readonly property var connectedDevice: Networking.devices.values.find(d => d.connected)
    readonly property var connectedNetwork: connectedDevice?.networks.values.find(n => n.connected)
    readonly property bool wireless: connectedDevice?.type === DeviceType.Wifi
    readonly property string networkIcon: !connectedDevice ? "wifi-off" : !wireless ? "ethernet" :
        (connectedNetwork?.signalStrength ?? 1) < 0.4 ? "wifi-weak" : "wifi"
    readonly property int battery: Math.round((UPower.displayDevice?.percentage ?? 0) * 100)
    SystemClock { id: clock; precision: SystemClock.Minutes }
    Rectangle {
        anchors.fill: parent; radius: 16; border.color: Theme.stroke
        gradient: Gradient {
            GradientStop { position: 0; color: "#d925334b" }
            GradientStop { position: 1; color: "#bb142034" }
        }
    }
    RowLayout {
        anchors { fill: parent; leftMargin: 8; rightMargin: 8 }
        spacing: 5
        ActionButton {
            iconSource: Quickshell.iconPath("fedora-logo-icon", "start-here")
            iconSize: 27; implicitWidth: 42; tooltip: "Applicazioni"
            onClicked: ShellState.toggle("launcher", bar.screen)
        }
        RowLayout {
            spacing: 0
            Repeater {
                model: bar.workspaces
                Button {
                    id: workspace
                    required property var modelData
                    readonly property bool active: bar.monitor?.activeWorkspace?.id === modelData.id
                    implicitWidth: active ? 46 : 28; implicitHeight: 34
                    Accessible.name: "Workspace " + modelData.id
                    ToolTip.visible: hovered
                    ToolTip.text: "Workspace " + modelData.id + " · " + modelData.toplevels.values.length + " finestre"
                    ToolTip.delay: 500
                    background: Rectangle { radius: 10; color: workspace.hovered || workspace.activeFocus ? Theme.raised : "transparent" }
                    contentItem: Item {
                        Rectangle {
                            anchors.centerIn: parent; width: workspace.active ? 28 : 8; height: 8; radius: 4
                            color: workspace.active ? Theme.accent : workspace.modelData.urgent ? Theme.danger : Theme.muted
                            Behavior on width { NumberAnimation { duration: 160 } }
                        }
                    }
                    onClicked: Hyprland.dispatch("hl.dsp.focus({ workspace = " + modelData.id + " })")
                }
            }
        }
        Text {
            Layout.fillWidth: true; Layout.minimumWidth: 0; Layout.leftMargin: 12
            text: Hyprland.activeToplevel?.title ?? "Desktop"
            elide: Text.ElideRight; textFormat: Text.PlainText
            color: Theme.muted; font.family: Theme.font; font.pixelSize: 12
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
            iconName: bar.networkIcon
            tooltip: bar.connectedDevice ? (bar.wireless ? "Wi-Fi connesso" : "Rete cablata connessa") : "Rete disconnessa"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton {
            iconName: Audio.muted || Audio.volume === 0 ? "volume-muted" : Audio.volume < 45 ? "volume-low" : "volume-high"
            tooltip: Audio.muted ? "Audio disattivato" : "Volume " + Audio.volume + "%"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton {
            visible: UPower.displayDevice?.isLaptopBattery ?? false
            iconName: !UPower.onBattery ? "battery-charging" : bar.battery < 20 ? "battery-low" : "battery"
            text: bar.battery + "%"
            tooltip: UPower.onBattery ? "Alimentazione a batteria" : "Alimentazione collegata"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        ActionButton {
            iconName: Notices.quiet ? "bell-off" : "bell"
            text: Notices.notifications.values.length > 0 ? String(Notices.notifications.values.length) : ""
            tooltip: Notices.quiet ? "Notifiche · Non disturbare" : "Notifiche"
            onClicked: ShellState.toggle("notifications", bar.screen)
        }
        Text {
            text: Qt.formatDateTime(clock.date, "ddd d MMM  HH:mm")
            color: Theme.text; font.family: Theme.font; font.pixelSize: 13
            Layout.leftMargin: 8; Layout.rightMargin: 8
        }
        ActionButton { iconName: "power"; tooltip: "Sessione"; onClicked: ShellState.toggle("power", bar.screen) }
    }
}

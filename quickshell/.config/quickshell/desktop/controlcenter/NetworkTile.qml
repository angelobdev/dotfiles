import QtQuick
import QtQuick.Layouts
import Quickshell.Networking
import ".."
import "../components"

ControlTile {
    id: root
    readonly property var device: Networking.devices.values.find(d => d.connected)
    readonly property var network: device?.networks.values.find(n => n.connected)
    ColumnLayout {
        anchors {
            fill: parent
            margins: 10
        }
        spacing: 2
        ActionButton {
            Layout.fillWidth: true
            alignLeft: true
            iconName: root.device?.type === DeviceType.Ethernet ? "ethernet" : "wifi"
            text: "Rete"
            tooltip: "Reti e Wi-Fi"
            onClicked: ShellState.toggle("network", ShellState.activeScreen)
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            text: network?.name || (Networking.wifiEnabled ? "Non connesso" : "Wi-Fi spento")
            elide: Text.ElideRight
            color: Theme.muted
            font.pixelSize: 11
            textFormat: Text.PlainText
        }
    }
}

import QtQuick
import QtQuick.Layouts
import Quickshell.Networking
import ".."
import "../components"
import "../services"

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
            iconName: NetworkInfo.icon(root.network)
            text: I18n.tr("network.label")
            tooltip: I18n.tr("network.tooltip")
            onClicked: ShellState.toggle("network", ShellState.activeScreen)
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            text: network?.name || (Networking.wifiEnabled ? I18n.tr("network.notConnected") : I18n.tr("network.wifiOff"))
            elide: Text.ElideRight
            color: Theme.muted
            font.pixelSize: 11
            textFormat: Text.PlainText
        }
    }
}

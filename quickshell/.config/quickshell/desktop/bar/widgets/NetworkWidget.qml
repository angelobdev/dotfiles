import QtQuick
import Quickshell.Networking
import "../.."
import "../../services"
import ".."

// The connection in use: Wi-Fi strength or cable; a click opens the Network panel.
BarButton {
    id: root
    property var bar
    property bool shown: true
    readonly property var device: Networking.devices.values.find(d => d.connected)
    readonly property var network: device?.networks.values.find(n => n.connected)
    iconName: network ? NetworkInfo.icon(network) : "wifi-off"
    tooltip: network?.name || (Networking.wifiEnabled ? I18n.tr("network.notConnected") : I18n.tr("network.wifiOff"))
    onClicked: ShellState.toggle("network", root.bar.screen)
}

import QtQuick
import QtQuick.Layouts
import Quickshell.Bluetooth
import ".."
import "../components"

ControlTile {
    readonly property int connected: Bluetooth.devices.values.filter(d => d.connected).length
    ColumnLayout {
        anchors {
            fill: parent
            margins: 10
        }
        spacing: 2
        ActionButton {
            Layout.fillWidth: true
            alignLeft: true
            iconName: "bluetooth"
            text: I18n.tr("bluetooth.title")
            tooltip: I18n.tr("bluetooth.devicesTitle")
            onClicked: ShellState.push("bluetooth")
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            text: !Bluetooth.defaultAdapter ? I18n.tr("common.unavailable") : !Bluetooth.defaultAdapter.enabled ? I18n.tr("common.off") : connected > 0 ? I18n.plural("bluetooth.connectedCount.one", "bluetooth.connectedCount.other", connected) : I18n.tr("common.on")
            elide: Text.ElideRight
            color: Theme.muted
            font.pixelSize: 11
        }
    }
}

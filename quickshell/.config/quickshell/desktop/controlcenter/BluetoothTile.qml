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
            text: I18n.tr("Bluetooth")
            tooltip: I18n.tr("Dispositivi Bluetooth")
            onClicked: ShellState.toggle("bluetooth", ShellState.activeScreen)
        }
        Text {
            Layout.fillWidth: true
            Layout.leftMargin: 12
            text: !Bluetooth.defaultAdapter ? I18n.tr("Non disponibile") : !Bluetooth.defaultAdapter.enabled ? I18n.tr("Spento") : connected > 0 ? I18n.plural("%1 connesso", "%1 connessi", connected) : I18n.tr("Acceso")
            elide: Text.ElideRight
            color: Theme.muted
            font.pixelSize: 11
        }
    }
}

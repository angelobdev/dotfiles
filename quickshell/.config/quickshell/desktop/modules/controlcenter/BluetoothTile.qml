import QtQuick
import QtQuick.Layouts
import Quickshell.Bluetooth
import "../.."
import "../../components"
ControlTile {
    readonly property int connected: Bluetooth.devices.values.filter(d => d.connected).length
    ColumnLayout {
        anchors { fill: parent; margins: 10 }
        spacing: 2
        ActionButton { Layout.fillWidth: true; alignLeft: true; iconName: "bluetooth"; text: "Bluetooth"; tooltip: "Dispositivi Bluetooth"; onClicked: ShellState.toggle("bluetooth", ShellState.activeScreen) }
        Text { Layout.fillWidth: true; Layout.leftMargin: 12; text: !Bluetooth.defaultAdapter ? "Non disponibile" : !Bluetooth.defaultAdapter.enabled ? "Spento" : connected > 0 ? connected + " connessi" : "Acceso"; elide: Text.ElideRight; color: Theme.muted; font.pixelSize: 11 }
    }
}

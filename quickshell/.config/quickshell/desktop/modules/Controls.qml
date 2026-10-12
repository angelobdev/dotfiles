import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Bluetooth
import ".."
import "../components"
Overlay {
    panelName: "controls"
    Card {
        anchors.centerIn: parent
        width: Math.min(580, parent.width - 48)
        height: Math.min(500, parent.height - 96)
        ColumnLayout {
            id: layout
            anchors { fill: parent; margins: 22 }
            spacing: 12
            Heading { text: "Centro di controllo" }
            RowLayout {
                ActionButton { text: "Rete"; iconName: "wifi"; onClicked: ShellState.toggle("network") }
                ActionButton { text: "Audio"; iconName: "volume-high"; onClicked: ShellState.toggle("audio") }
                ActionButton { text: "Batteria"; iconName: "battery"; onClicked: ShellState.toggle("battery") }
            }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true; clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width; spacing: 12
                    Heading { text: "Bluetooth" }
                    RowLayout {
                        ActionButton { text: Bluetooth.defaultAdapter?.enabled ? "Bluetooth acceso" : "Bluetooth spento"; enabled: !!Bluetooth.defaultAdapter; highlighted: Bluetooth.defaultAdapter?.enabled ?? false; onClicked: Bluetooth.defaultAdapter.enabled = !Bluetooth.defaultAdapter.enabled }
                        Text { text: "Dispositivi già associati"; color: Theme.muted }
                    }
                    Repeater {
                        model: Bluetooth.devices.values.filter(d => d.paired)
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true
                            enabled: Bluetooth.defaultAdapter?.enabled ?? false
                            text: (modelData.connected ? "● " : "○ ") + modelData.name + " · " + BluetoothDeviceState.toString(modelData.state)
                            highlighted: modelData.connected
                            onClicked: modelData.connected = !modelData.connected
                        }
                    }
                    Text { visible: !Bluetooth.defaultAdapter; text: "Nessun adattatore Bluetooth"; color: Theme.muted }
                }
            }
            ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
        }
    }
}

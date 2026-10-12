import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Bluetooth
import ".."
import "../components"
Overlay {
    id: root
    panelName: "bluetooth"
    Card {
        anchors { top: parent.top; right: parent.right; topMargin: 58; rightMargin: 12 }
        width: Math.min(460, parent.width - 24)
        height: Math.min(500, parent.height - 76)
        ColumnLayout {
            anchors { fill: parent; margins: 20 }
            spacing: 12
            RowLayout {
                ActionButton { text: "‹"; tooltip: "Centro di controllo"; onClicked: ShellState.toggle("controls", ShellState.activeScreen) }
                Heading { text: "Bluetooth"; Layout.fillWidth: true }
                ActionButton { text: "×"; tooltip: "Chiudi"; onClicked: ShellState.close() }
            }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
                ColumnLayout {
                    width: parent.width; spacing: 12
                    Repeater {
                        model: Bluetooth.adapters
                        ColumnLayout {
                            id: adapterGroup
                            required property var modelData
                            readonly property var paired: modelData.devices.values.filter(d => d.paired).sort((a,b) => Number(b.connected)-Number(a.connected) || a.name.localeCompare(b.name))
                            Layout.fillWidth: true; spacing: 8
                            RowLayout {
                                Text { text: adapterGroup.modelData.name; Layout.fillWidth: true; elide: Text.ElideRight; color: Theme.text; textFormat: Text.PlainText }
                                ControlSwitch { checked: adapterGroup.modelData.enabled; enabled: ![BluetoothAdapterState.Blocked, BluetoothAdapterState.Enabling, BluetoothAdapterState.Disabling].includes(adapterGroup.modelData.state); onToggled: adapterGroup.modelData.enabled = checked; Accessible.name: "Bluetooth " + adapterGroup.modelData.name; palette.highlight: Theme.accent }
                            }
                            Text { text: adapterGroup.modelData.state === BluetoothAdapterState.Blocked ? "Bloccato dall’hardware" : adapterGroup.modelData.enabled ? "Dispositivi associati" : "Bluetooth spento"; color: Theme.muted; font.pixelSize: 12 }
                            Repeater {
                                model: adapterGroup.paired
                                ColumnLayout {
                                    required property var modelData
                                    Layout.fillWidth: true; spacing: 2
                                    ActionButton {
                                        Layout.fillWidth: true; alignLeft: true; iconName: "bluetooth"; text: modelData.name; tooltip: modelData.address
                                        highlighted: modelData.connected
                                        enabled: adapterGroup.modelData.enabled && !modelData.blocked && ![BluetoothDeviceState.Connecting, BluetoothDeviceState.Disconnecting].includes(modelData.state)
                                        onClicked: modelData.connected = !modelData.connected
                                    }
                                    Text { text: (modelData.state === BluetoothDeviceState.Connected ? "Connesso" : modelData.state === BluetoothDeviceState.Connecting ? "Connessione…" : modelData.state === BluetoothDeviceState.Disconnecting ? "Disconnessione…" : "Disconnesso") + (modelData.batteryAvailable ? " · " + Math.round(modelData.battery * 100) + "%" : ""); color: Theme.muted; font.pixelSize: 11; Layout.leftMargin: 12 }
                                }
                            }
                            Text { visible: adapterGroup.paired.length === 0; text: "Nessun dispositivo già associato"; color: Theme.muted; font.pixelSize: 12 }
                        }
                    }
                    Text { visible: Bluetooth.adapters.values.length === 0; text: "Nessun adattatore Bluetooth disponibile"; color: Theme.muted; wrapMode: Text.Wrap; Layout.fillWidth: true }
                }
            }
            Text { text: "Il pannello connette i dispositivi già associati. L’associazione con PIN o conferma sarà aggiunta con un agente dedicato."; color: Theme.muted; font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true }
        }
    }
}

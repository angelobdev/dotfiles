import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Bluetooth
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "bluetooth"
    onVisibleChanged: if (!visible) {
        for (const adapter of Bluetooth.adapters.values)
            adapter.discovering = false;
    }
    SidePanelCard {
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("bluetooth.title")
                showBack: true
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth
                clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 12
                    Repeater {
                        model: Bluetooth.adapters
                        ColumnLayout {
                            id: adapterGroup
                            required property var modelData
                            readonly property var discovered: modelData.devices.values.filter(d => !d.paired).sort((a, b) => a.name.localeCompare(b.name))
                            readonly property var paired: modelData.devices.values.filter(d => d.paired).sort((a, b) => Number(b.connected) - Number(a.connected) || a.name.localeCompare(b.name))
                            Layout.fillWidth: true
                            spacing: 8
                            RowLayout {
                                Text {
                                    text: adapterGroup.modelData.name
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: Theme.text
                                    textFormat: Text.PlainText
                                }
                                ControlSwitch {
                                    checked: adapterGroup.modelData.enabled
                                    enabled: ![BluetoothAdapterState.Blocked, BluetoothAdapterState.Enabling, BluetoothAdapterState.Disabling].includes(adapterGroup.modelData.state)
                                    onToggled: adapterGroup.modelData.enabled = checked
                                    Accessible.name: I18n.tr("osd.bluetoothPrefix") + adapterGroup.modelData.name
                                }
                            }
                            ActionButton {
                                Layout.fillWidth: true
                                text: adapterGroup.modelData.discovering ? I18n.tr("bluetooth.stopScan") : I18n.tr("bluetooth.scan")
                                iconName: adapterGroup.modelData.discovering ? "stop" : "bluetooth"
                                enabled: adapterGroup.modelData.enabled && BluetoothAgent.registered
                                highlighted: adapterGroup.modelData.discovering
                                onClicked: adapterGroup.modelData.discovering = !adapterGroup.modelData.discovering
                            }
                            Text {
                                text: adapterGroup.modelData.state === BluetoothAdapterState.Blocked ? I18n.tr("bluetooth.hardwareBlocked") : adapterGroup.modelData.enabled ? I18n.tr("bluetooth.pairedDevices") : I18n.tr("bluetooth.off")
                                color: Theme.muted
                                font.pixelSize: 12
                            }
                            Repeater {
                                model: adapterGroup.paired
                                ColumnLayout {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    spacing: 2
                                    ActionButton {
                                        Layout.fillWidth: true
                                        alignLeft: true
                                        iconSource: Quickshell.iconPath(modelData.icon || "bluetooth", "bluetooth")
                                        text: modelData.name
                                        tooltip: modelData.address
                                        highlighted: modelData.connected
                                        enabled: adapterGroup.modelData.enabled && !modelData.blocked && ![BluetoothDeviceState.Connecting, BluetoothDeviceState.Disconnecting].includes(modelData.state)
                                        onClicked: modelData.connected = !modelData.connected
                                    }
                                    Text {
                                        text: (modelData.state === BluetoothDeviceState.Connected ? I18n.tr("bluetooth.connected") : modelData.state === BluetoothDeviceState.Connecting ? I18n.tr("bluetooth.connecting") : modelData.state === BluetoothDeviceState.Disconnecting ? I18n.tr("bluetooth.disconnecting") : I18n.tr("bluetooth.disconnected")) + (modelData.batteryAvailable ? " · " + Math.round(modelData.battery * 100) + "%" : "")
                                        color: Theme.muted
                                        font.pixelSize: 11
                                        Layout.leftMargin: 12
                                    }
                                }
                            }
                            Text {
                                visible: adapterGroup.discovered.length > 0
                                text: I18n.tr("bluetooth.availableDevices")
                                color: Theme.muted
                                font.pixelSize: 12
                            }
                            Repeater {
                                model: adapterGroup.discovered
                                RowLayout {
                                    required property var modelData
                                    readonly property bool pairing: modelData.pairing || BluetoothAgent.pairing.includes(modelData.dbusPath)
                                    Layout.fillWidth: true
                                    ActionButton {
                                        Layout.fillWidth: true
                                        alignLeft: true
                                        iconSource: Quickshell.iconPath(modelData.icon || "bluetooth", "bluetooth")
                                        text: modelData.name + (parent.pairing ? I18n.tr("bluetooth.pairingSuffix") : "")
                                        tooltip: modelData.address
                                        enabled: adapterGroup.modelData.enabled && BluetoothAgent.registered && !parent.pairing && !modelData.blocked
                                        onClicked: BluetoothAgent.pair(modelData)
                                    }
                                    PanelIconButton {
                                        visible: parent.pairing
                                        iconName: "close"
                                        tooltip: I18n.tr("bluetooth.cancelPairing")
                                        onClicked: BluetoothAgent.cancel(modelData.dbusPath)
                                    }
                                }
                            }
                            Text {
                                visible: adapterGroup.paired.length === 0
                                text: I18n.tr("bluetooth.noPairedDevices")
                                color: Theme.muted
                                font.pixelSize: 12
                            }
                        }
                    }
                    Text {
                        visible: Bluetooth.adapters.values.length === 0
                        text: I18n.tr("bluetooth.noAdapters")
                        color: Theme.muted
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                }
            }
            Text {
                text: BluetoothAgent.error || I18n.tr("bluetooth.pairingHint")
                color: BluetoothAgent.error ? Theme.danger : Theme.muted
                textFormat: Text.PlainText
                font.pixelSize: 11
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
    }
}

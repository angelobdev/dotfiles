import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Networking
import Quickshell.Bluetooth
import Quickshell.Services.UPower
import ".."
import "../components"
import "../services"
Overlay {
    id: root
    panelName: "controls"
    property var passwordNetwork: null
    property string error: ""
    readonly property var wifiDevices: Networking.devices.values.filter(d => d.type === DeviceType.Wifi)
    function personal(network) {
        return [WifiSecurityType.WpaPsk, WifiSecurityType.Wpa2Psk, WifiSecurityType.Sae].includes(network.security);
    }
    onVisibleChanged: if (!visible) { passwordNetwork = null; password.clear(); error = ""; }
    Connections { target: root.passwordNetwork; function onConnectedChanged() { if (root.passwordNetwork?.connected) { root.passwordNetwork = null; password.clear(); } } }
    Variants {
        model: root.wifiDevices
        delegate: QtObject {
            required property var modelData
            // Only scan while the user is looking at the network panel.
            property var scanBinding: Binding { target: modelData; property: "scannerEnabled"; value: root.visible && Networking.wifiEnabled }
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(660, parent.width - 48)
        height: Math.min(740, parent.height - 96)
        ColumnLayout {
            anchors { fill: parent; margins: 22 }
            spacing: 12
            Heading { text: "Centro di controllo" }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 14
                    Heading { text: "Audio" }
                    RowLayout {
                        ActionButton { text: Audio.muted ? "Riattiva audio" : "Muto"; enabled: !!Audio.sink; onClicked: Audio.toggleMute() }
                        Slider { Layout.fillWidth: true; from: 0; to: 1; value: Audio.volume / 100; enabled: !!Audio.sink; onMoved: Audio.setVolume(value) }
                        Text { text: Audio.volume + "%"; color: Theme.text }
                        ActionButton { text: Audio.source?.audio?.muted ? "Mic ×" : "Mic ●"; enabled: !!Audio.source; onClicked: Audio.toggleMic() }
                    }
                    Text { Layout.fillWidth: true; text: Audio.sink?.description ?? "Nessuna uscita audio"; color: Theme.muted; elide: Text.ElideRight; textFormat: Text.PlainText }
                    Heading { text: "Rete" }
                    RowLayout {
                        ActionButton { text: Networking.wifiEnabled ? "Wi-Fi acceso" : "Wi-Fi spento"; enabled: Networking.wifiHardwareEnabled; highlighted: Networking.wifiEnabled; onClicked: Networking.wifiEnabled = !Networking.wifiEnabled }
                        Text { text: NetworkConnectivity.toString(Networking.connectivity); color: Theme.muted }
                    }
                    Repeater {
                        model: Networking.devices
                        ColumnLayout {
                            id: deviceRow
                            required property var modelData
                            Layout.fillWidth: true
                            Text { text: deviceRow.modelData.name + " · " + ConnectionState.toString(deviceRow.modelData.state); color: Theme.muted; textFormat: Text.PlainText }
                            Repeater {
                                model: deviceRow.modelData.networks
                                ActionButton {
                                    id: networkRow
                                    required property var modelData
                                    Layout.fillWidth: true
                                    text: (modelData.connected ? "● " : "○ ") + modelData.name + (modelData.stateChanging ? " …" : "")
                                    highlighted: modelData.connected
                                    enabled: !modelData.stateChanging
                                    onClicked: {
                                        root.error = "";
                                        if (modelData.connected) { modelData.disconnect(); return; }
                                        if (modelData.known || deviceRow.modelData.type !== DeviceType.Wifi || modelData.security === WifiSecurityType.Open || modelData.security === WifiSecurityType.Owe) modelData.connect();
                                        else if (root.personal(modelData)) { root.passwordNetwork = modelData; password.clear(); password.forceActiveFocus(); }
                                        else root.error = "Per questa rete serve un profilo Enterprise già configurato.";
                                    }
                                    Connections {
                                        target: networkRow.modelData
                                        function onConnectionFailed(reason) {
                                            root.error = "Connessione fallita: " + ConnectionFailReason.toString(reason);
                                            if (root.personal(networkRow.modelData) && reason === ConnectionFailReason.NoSecrets) {
                                                root.passwordNetwork = networkRow.modelData; password.clear(); password.forceActiveFocus();
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Text { visible: Networking.devices.values.length === 0; text: "Nessuna interfaccia gestita da NetworkManager"; color: Theme.muted }
                    ColumnLayout {
                        visible: root.passwordNetwork !== null
                        Layout.fillWidth: true
                        Text { text: "Password per " + (root.passwordNetwork?.name ?? ""); color: Theme.text; textFormat: Text.PlainText }
                        RowLayout {
                            InputField { id: password; Layout.fillWidth: true; echoMode: TextInput.Password; placeholderText: "Password Wi-Fi"; onAccepted: connectButton.clicked() }
                            ActionButton {
                                id: connectButton
                                text: "Connetti"
                                enabled: !!root.passwordNetwork && password.text.length > 0
                                onClicked: if (enabled) { root.passwordNetwork.connectWithPsk(password.text); password.clear(); }
                            }
                            ActionButton { text: "Annulla"; onClicked: { root.passwordNetwork = null; password.clear(); } }
                        }
                    }
                    Text { visible: root.error !== ""; text: root.error; color: Theme.danger; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
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
                    Heading { text: "Energia" }
                    Text { text: UPower.onBattery ? "Alimentazione a batteria" : "Alimentazione esterna"; color: Theme.muted }
                    RowLayout {
                        ActionButton { text: "Risparmio"; highlighted: PowerProfiles.profile === PowerProfile.PowerSaver; onClicked: PowerProfiles.profile = PowerProfile.PowerSaver }
                        ActionButton { text: "Bilanciato"; highlighted: PowerProfiles.profile === PowerProfile.Balanced; onClicked: PowerProfiles.profile = PowerProfile.Balanced }
                        ActionButton { text: "Prestazioni"; enabled: PowerProfiles.hasPerformanceProfile; highlighted: PowerProfiles.profile === PowerProfile.Performance; onClicked: PowerProfiles.profile = PowerProfile.Performance }
                    }
                }
            }
            ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
        }
    }
}

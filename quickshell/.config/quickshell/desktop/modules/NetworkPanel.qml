import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Networking
import ".."
import "../components"
import "../services"
Overlay {
    id: root
    panelName: "network"
    property var passwordNetwork: null
    property string error: ""
    readonly property var wifiDevices: Networking.devices.values.filter(d => d.type === DeviceType.Wifi)
    function personal(network) {
        return [WifiSecurityType.WpaPsk, WifiSecurityType.Wpa2Psk, WifiSecurityType.Sae].includes(network.security);
    }
    onOpened: { search.clear(); search.forceActiveFocus(); }
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
            Heading { text: "Rete e Wi-Fi" }
            InputField {
                id: search; Layout.fillWidth: true; placeholderText: "Cerca una rete Wi-Fi…"
            }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 14
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
                                model: deviceRow.modelData.networks.values.filter(n => n.name.toLowerCase().includes(search.text.toLowerCase()))
                                    .sort((a, b) => Number(b.connected) - Number(a.connected) || (b.signalStrength ?? 0) - (a.signalStrength ?? 0) || a.name.localeCompare(b.name))
                                ActionButton {
                                    id: networkRow
                                    required property var modelData
                                    Layout.fillWidth: true
                                    alignLeft: true
                                    iconName: deviceRow.modelData.type === DeviceType.Wifi ? "wifi" : "ethernet"
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
                                onClicked: if (enabled) { root.error = ""; root.passwordNetwork.connectWithPsk(password.text); password.clear(); }
                            }
                            ActionButton { text: "Annulla"; onClicked: { root.passwordNetwork = null; password.clear(); } }
                        }
                    }
                    Text { visible: root.error !== ""; text: root.error; color: Theme.danger; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
                }
            }
            RowLayout {
                ActionButton { text: "‹ Centro di controllo"; onClicked: ShellState.toggle("controls", ShellState.activeScreen) }
                Item { Layout.fillWidth: true }
                ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
            }
        }
    }
}

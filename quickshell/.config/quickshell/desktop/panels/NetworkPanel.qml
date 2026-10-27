import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Networking
import ".."
import "../components"

Overlay {
    id: root
    panelName: "network"
    property var passwordNetwork: null
    property string error: ""
    readonly property var wifiDevices: Networking.devices.values.filter(d => d.type === DeviceType.Wifi)
    function personal(network) {
        return [WifiSecurityType.WpaPsk, WifiSecurityType.Wpa2Psk, WifiSecurityType.Sae].includes(network.security);
    }
    function askPassword(network) {
        passwordNetwork = network;
        password.clear();
        password.forceActiveFocus();
    }
    function cancelPassword() {
        passwordNetwork = null;
        password.clear();
    }
    onOpened: {
        search.clear();
        search.forceActiveFocus();
    }
    onVisibleChanged: if (!visible) {
        cancelPassword();
        error = "";
    }
    Connections {
        target: root.passwordNetwork
        function onConnectedChanged() {
            if (root.passwordNetwork?.connected) {
                root.cancelPassword();
            }
        }
    }
    Variants {
        model: root.wifiDevices
        delegate: QtObject {
            required property var modelData
            // Only scan while the user is looking at the network panel.
            property var scanBinding: Binding {
                target: modelData
                property: "scannerEnabled"
                value: root.visible && Networking.wifiEnabled
            }
        }
    }
    SidePanelCard {
        ColumnLayout {
            anchors {
                fill: parent
                margins: 16
            }
            spacing: 12
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("network.title")
                showBack: true
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: I18n.tr("network.searchPlaceholder")
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 14
                    RowLayout {
                        ActionButton {
                            iconName: Networking.wifiEnabled ? "wifi" : "wifi-off"
                            text: Networking.wifiEnabled ? I18n.tr("network.wifiOn") : I18n.tr("network.wifiOff")
                            enabled: Networking.wifiHardwareEnabled
                            highlighted: Networking.wifiEnabled
                            onClicked: Networking.wifiEnabled = !Networking.wifiEnabled
                        }
                        Text {
                            text: I18n.networkDescription(NetworkConnectivity.toString(Networking.connectivity))
                            color: Theme.muted
                            font.pixelSize: 11
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }
                    Repeater {
                        model: Networking.devices
                        ColumnLayout {
                            id: deviceRow
                            required property var modelData
                            Layout.fillWidth: true
                            Text {
                                text: deviceRow.modelData.name + " · " + I18n.networkDescription(ConnectionState.toString(deviceRow.modelData.state))
                                color: Theme.muted
                                textFormat: Text.PlainText
                                font.pixelSize: 11
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            Repeater {
                                model: deviceRow.modelData.networks.values.filter(n => n.name.toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => Number(b.connected) - Number(a.connected) || (b.signalStrength ?? 0) - (a.signalStrength ?? 0) || a.name.localeCompare(b.name))
                                ActionButton {
                                    id: networkRow
                                    required property var modelData
                                    Layout.fillWidth: true
                                    alignLeft: true
                                    iconName: deviceRow.modelData.type === DeviceType.Wifi ? "wifi" : "ethernet"
                                    text: modelData.name + (modelData.stateChanging ? " …" : "")
                                    highlighted: modelData.connected
                                    enabled: !modelData.stateChanging
                                    onClicked: {
                                        root.error = "";
                                        if (modelData.connected) {
                                            modelData.disconnect();
                                            return;
                                        }
                                        if (modelData.known || deviceRow.modelData.type !== DeviceType.Wifi || modelData.security === WifiSecurityType.Open || modelData.security === WifiSecurityType.Owe)
                                            modelData.connect();
                                        else if (root.personal(modelData))
                                            root.askPassword(modelData);
                                        else
                                            root.error = I18n.tr("network.errors.enterpriseProfileRequired");
                                    }
                                    Connections {
                                        target: networkRow.modelData
                                        function onConnectionFailed(reason) {
                                            root.error = I18n.tr("network.connectionFailedPrefix") + I18n.networkDescription(ConnectionFailReason.toString(reason));
                                            if (root.personal(networkRow.modelData) && reason === ConnectionFailReason.NoSecrets)
                                                root.askPassword(networkRow.modelData);
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Text {
                        visible: Networking.devices.values.length === 0
                        text: I18n.tr("network.noDevices")
                        color: Theme.muted
                    }
                    ColumnLayout {
                        visible: root.passwordNetwork !== null
                        Layout.fillWidth: true
                        Text {
                            text: I18n.tr("network.passwordPrefix") + (root.passwordNetwork?.name ?? "")
                            color: Theme.text
                            textFormat: Text.PlainText
                        }
                        InputField {
                            id: password
                            Layout.fillWidth: true
                            echoMode: TextInput.Password
                            placeholderText: I18n.tr("network.passwordPlaceholder")
                            onAccepted: connectButton.clicked()
                        }
                        RowLayout {
                            ActionButton {
                                id: connectButton
                                text: I18n.tr("network.connect")
                                enabled: !!root.passwordNetwork && password.text.length > 0
                                onClicked: if (enabled) {
                                    root.error = "";
                                    root.passwordNetwork.connectWithPsk(password.text);
                                    password.clear();
                                }
                            }
                            ActionButton {
                                text: I18n.tr("common.cancel")
                                onClicked: root.cancelPassword()
                            }
                        }
                    }
                    Text {
                        visible: root.error !== ""
                        text: root.error
                        color: Theme.danger
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        textFormat: Text.PlainText
                    }
                }
            }
        }
    }
}

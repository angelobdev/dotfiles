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
    closeOnEscape: false
    property var passwordNetwork: null
    property var detailsNetwork: null
    property var hiddenDevice: null
    property bool hiddenSecure: true
    property string error: ""
    readonly property var wifiDevices: Networking.devices.values.filter(d => d.type === DeviceType.Wifi)
    readonly property var activeDevice: Networking.devices.values.find(d => d.connected) ?? null
    readonly property var activeNetwork: activeDevice?.networks.values.find(n => n.connected) ?? null
    readonly property var activeInfo: NetworkInfo.details[activeDevice?.name ?? ""] ?? null
    readonly property string tailscaleSummary: {
        const tailscale = NetworkInfo.tailscale;
        if (tailscale.state === "Running")
            return [I18n.tr("network.tailscaleConnected", [tailscale.address]), I18n.tr("network.tailscalePeers", [tailscale.online, tailscale.peers]), tailscale.exitNode ? I18n.tr("network.tailscaleExitNode", [tailscale.exitNode]) : ""].filter(part => part !== "").join(" · ");
        if (tailscale.state === "Stopped")
            return I18n.tr("network.tailscaleOff");
        if (tailscale.state === "NeedsLogin")
            return I18n.tr("network.tailscaleNeedsLogin");
        return I18n.tr("network.tailscaleStarting");
    }
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
    function openHidden(device) {
        cancelPassword();
        error = "";
        hiddenSecure = true;
        hiddenSsid.clear();
        hiddenPassword.clear();
        hiddenDevice = device;
        hiddenSsid.forceActiveFocus();
    }
    function cancelHidden() {
        hiddenDevice = null;
        hiddenSsid.clear();
        hiddenPassword.clear();
    }
    function openDetails(network) {
        cancelPassword();
        error = "";
        detailsNetwork = network;
        scroll.ScrollBar.vertical.position = 0;
        if (network.connected)
            NetworkInfo.refreshDetails(network.device?.name);
    }
    function closeDetails() {
        detailsNetwork = null;
        scroll.ScrollBar.vertical.position = 0;
        search.forceActiveFocus();
    }
    onOpened: {
        search.clear();
        search.forceActiveFocus();
        NetworkInfo.refreshDetails(activeDevice?.name);
        NetworkInfo.refreshExtras();
    }
    onVisibleChanged: if (!visible) {
        cancelPassword();
        cancelHidden();
        hotspotPassword.reset();
        detailsNetwork = null;
        error = "";
    }
    onActiveNetworkChanged: if (visible)
        NetworkInfo.refreshDetails(activeDevice?.name)
    contentItem.Keys.onEscapePressed: {
        if (detailsNetwork)
            closeDetails();
        else
            ShellState.close();
    }
    Connections {
        target: root.passwordNetwork
        function onConnectedChanged() {
            if (root.passwordNetwork?.connected) {
                root.cancelPassword();
            }
        }
    }
    Connections {
        target: NetworkInfo
        function onJoined() {
            root.cancelHidden();
        }
    }
    // VPN, hotspot and Tailscale state are not exposed by Quickshell.Networking; poll only while the list is open.
    Timer {
        interval: 4000
        running: root.visible && root.detailsNetwork === null
        repeat: true
        onTriggered: NetworkInfo.refreshExtras()
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
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                Layout.fillWidth: true
                title: root.detailsNetwork?.name ?? I18n.tr("network.title")
                showBack: true
                backToControls: root.detailsNetwork === null
                backTooltip: root.detailsNetwork ? I18n.tr("network.title") : I18n.tr("controlCenter.title")
                onBack: root.closeDetails()
            }
            InputField {
                id: search
                visible: root.detailsNetwork === null
                Layout.fillWidth: true
                placeholderText: I18n.tr("network.searchPlaceholder")
            }
            ScrollView {
                id: scroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 14
                    Loader {
                        active: root.detailsNetwork !== null
                        visible: active
                        Layout.fillWidth: true
                        sourceComponent: NetworkDetails {
                            network: root.detailsNetwork
                            onForgotten: root.closeDetails()
                        }
                    }
                    RowLayout {
                        visible: root.detailsNetwork === null
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
                    ColumnLayout {
                        visible: root.detailsNetwork === null && root.activeNetwork !== null
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: I18n.tr("network.currentConnection")
                            color: Theme.muted
                            font.pixelSize: 11
                        }
                        ActionButton {
                            id: currentConnection
                            Layout.fillWidth: true
                            implicitHeight: 58
                            text: root.activeNetwork?.name ?? ""
                            tooltip: I18n.tr("network.details")
                            onClicked: root.openDetails(root.activeNetwork)
                            background: Rectangle {
                                radius: 12
                                color: currentConnection.down || currentConnection.hovered || currentConnection.activeFocus ? Theme.raised : Theme.tile
                            }
                            contentItem: RowLayout {
                                spacing: 12
                                Icon {
                                    name: NetworkInfo.icon(root.activeNetwork)
                                    Layout.preferredWidth: 22
                                    Layout.preferredHeight: 22
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Text {
                                        Layout.fillWidth: true
                                        text: currentConnection.text
                                        color: Theme.text
                                        font.family: Theme.font
                                        font.pixelSize: 14
                                        elide: Text.ElideRight
                                        textFormat: Text.PlainText
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: [(root.activeInfo?.ipv4 ?? []).map(a => a.split("/")[0])[0] ?? "", root.activeInfo?.frequency ? I18n.tr("network.band", [(root.activeInfo.frequency / 1000).toLocaleString(I18n.locale, "f", 1), root.activeInfo.channel]) : root.activeDevice?.type === DeviceType.Wired && root.activeDevice.linkSpeed > 0 ? I18n.tr("network.linkSpeedValue", [root.activeDevice.linkSpeed]) : ""].filter(part => part !== "").join(" · ")
                                        color: Theme.muted
                                        font.family: Theme.font
                                        font.pixelSize: 11
                                        elide: Text.ElideRight
                                    }
                                }
                                Icon {
                                    name: "chevron-right"
                                    color: Theme.muted
                                    Layout.preferredWidth: 16
                                    Layout.preferredHeight: 16
                                }
                            }
                        }
                    }
                    Repeater {
                        model: root.detailsNetwork === null ? Networking.devices : []
                        ColumnLayout {
                            id: deviceRow
                            required property var modelData
                            readonly property bool wired: modelData.type === DeviceType.Wired
                            Layout.fillWidth: true
                            Text {
                                text: [deviceRow.wired ? I18n.tr("network.ethernet") + " (" + deviceRow.modelData.name + ")" : deviceRow.modelData.name, deviceRow.wired && !deviceRow.modelData.hasLink ? I18n.tr("network.cableUnplugged") : I18n.networkDescription(ConnectionState.toString(deviceRow.modelData.state))].join(" · ")
                                color: Theme.muted
                                textFormat: Text.PlainText
                                font.pixelSize: 11
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            Repeater {
                                model: deviceRow.modelData.networks.values.filter(n => n.name.toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => Number(b.connected) - Number(a.connected) || (b.signalStrength ?? 0) - (a.signalStrength ?? 0) || a.name.localeCompare(b.name))
                                RowLayout {
                                    id: networkRow
                                    required property var modelData
                                    readonly property bool secured: !deviceRow.wired && modelData.security !== WifiSecurityType.Open && modelData.security !== WifiSecurityType.Owe
                                    Layout.fillWidth: true
                                    spacing: 2
                                    ActionButton {
                                        Layout.fillWidth: true
                                        alignLeft: true
                                        iconName: NetworkInfo.icon(networkRow.modelData)
                                        text: networkRow.modelData.name + (networkRow.modelData.stateChanging ? " …" : "")
                                        highlighted: networkRow.modelData.connected
                                        enabled: !networkRow.modelData.stateChanging
                                        onClicked: {
                                            root.error = "";
                                            if (networkRow.modelData.connected) {
                                                networkRow.modelData.disconnect();
                                                return;
                                            }
                                            if (networkRow.modelData.known || deviceRow.wired || !networkRow.secured)
                                                networkRow.modelData.connect();
                                            else if (root.personal(networkRow.modelData))
                                                root.askPassword(networkRow.modelData);
                                            else
                                                root.error = I18n.tr("network.errors.enterpriseProfileRequired");
                                        }
                                    }
                                    Icon {
                                        visible: networkRow.secured && !networkRow.modelData.known
                                        name: "lock"
                                        color: Theme.muted
                                        Layout.preferredWidth: 14
                                        Layout.preferredHeight: 14
                                        Layout.rightMargin: 7
                                    }
                                    CompactIconButton {
                                        visible: networkRow.modelData.known
                                        iconName: "chevron-right"
                                        iconSize: 16
                                        tooltip: I18n.tr("network.details")
                                        onClicked: root.openDetails(networkRow.modelData)
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
                            ActionButton {
                                visible: !deviceRow.wired && search.text === "" && root.hiddenDevice === null
                                Layout.fillWidth: true
                                alignLeft: true
                                // Line the label up with the network names next to their icons.
                                leftPadding: 42
                                text: I18n.tr("network.otherNetwork")
                                onClicked: root.openHidden(deviceRow.modelData)
                            }
                        }
                    }
                    ColumnLayout {
                        visible: root.detailsNetwork === null && (NetworkInfo.vpns.length > 0 || NetworkInfo.tailscale.installed === true)
                        Layout.fillWidth: true
                        Text {
                            text: I18n.tr("network.vpn")
                            color: Theme.muted
                            font.pixelSize: 11
                        }
                        RowLayout {
                            visible: NetworkInfo.tailscale.installed === true
                            Layout.fillWidth: true
                            spacing: 10
                            Icon {
                                name: "vpn"
                                Layout.leftMargin: 12
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Text {
                                    text: I18n.tr("network.tailscale")
                                    color: Theme.text
                                    font.family: Theme.font
                                    font.pixelSize: 13
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: root.tailscaleSummary
                                    color: Theme.muted
                                    font.pixelSize: 11
                                    elide: Text.ElideRight
                                    textFormat: Text.PlainText
                                }
                            }
                            ControlSwitch {
                                enabled: !NetworkInfo.busy && ["Running", "Stopped"].includes(NetworkInfo.tailscale.state)
                                onToggled: NetworkInfo.run(checked ? "tailscale-up" : "tailscale-down", [])
                                Accessible.name: I18n.tr("network.tailscale")
                                Binding on checked {
                                    value: NetworkInfo.tailscale.state === "Running"
                                    when: !NetworkInfo.busy
                                }
                            }
                        }
                        Repeater {
                            model: NetworkInfo.vpns
                            ActionButton {
                                required property var modelData
                                Layout.fillWidth: true
                                alignLeft: true
                                iconName: "vpn"
                                text: modelData.name
                                highlighted: modelData.active
                                enabled: !NetworkInfo.busy
                                onClicked: NetworkInfo.run(modelData.active ? "vpn-down" : "vpn-up", [modelData.uuid])
                            }
                        }
                    }
                    ColumnLayout {
                        visible: root.detailsNetwork === null && root.wifiDevices.length > 0
                        Layout.fillWidth: true
                        spacing: 8
                        Text {
                            text: I18n.tr("network.hotspot")
                            color: Theme.muted
                            font.pixelSize: 11
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Icon {
                                name: "hotspot"
                                Layout.leftMargin: 12
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                            }
                            Text {
                                Layout.fillWidth: true
                                text: NetworkInfo.hotspot.active ? I18n.tr("network.hotspotOn", [NetworkInfo.hotspot.ssid]) : I18n.tr("network.hotspotHint")
                                color: NetworkInfo.hotspot.active ? Theme.text : Theme.muted
                                font.family: Theme.font
                                font.pixelSize: NetworkInfo.hotspot.active ? 13 : 11
                                wrapMode: Text.Wrap
                                textFormat: Text.PlainText
                            }
                            ControlSwitch {
                                enabled: !NetworkInfo.busy
                                onToggled: NetworkInfo.run(checked ? "hotspot-on" : "hotspot-off", checked ? [root.wifiDevices[0].name] : [])
                                Accessible.name: I18n.tr("network.hotspot")
                                Binding on checked {
                                    value: NetworkInfo.hotspot.active === true
                                    when: !NetworkInfo.busy
                                }
                            }
                        }
                        NetworkPassword {
                            id: hotspotPassword
                            visible: NetworkInfo.hotspot.active === true
                            Layout.fillWidth: true
                            uuid: NetworkInfo.hotspot.uuid ?? ""
                            name: NetworkInfo.hotspot.ssid ?? ""
                        }
                    }
                    ColumnLayout {
                        visible: root.detailsNetwork === null && root.hiddenDevice !== null
                        Layout.fillWidth: true
                        spacing: 8
                        Text {
                            text: I18n.tr("network.otherNetwork")
                            color: Theme.text
                        }
                        InputField {
                            id: hiddenSsid
                            Layout.fillWidth: true
                            placeholderText: I18n.tr("network.ssidPlaceholder")
                            onAccepted: root.hiddenSecure ? hiddenPassword.forceActiveFocus() : joinButton.clicked()
                        }
                        ChoiceChips {
                            options: [
                                {
                                    name: "personal",
                                    label: I18n.tr("network.securityPersonal")
                                },
                                {
                                    name: "open",
                                    label: I18n.tr("network.securityNone")
                                }
                            ]
                            current: root.hiddenSecure ? "personal" : "open"
                            onChosen: name => root.hiddenSecure = name === "personal"
                        }
                        InputField {
                            id: hiddenPassword
                            visible: root.hiddenSecure
                            Layout.fillWidth: true
                            echoMode: TextInput.Password
                            placeholderText: I18n.tr("network.passwordPlaceholder")
                            onAccepted: joinButton.clicked()
                        }
                        RowLayout {
                            ActionButton {
                                id: joinButton
                                text: NetworkInfo.joining ? I18n.tr("network.joining") : I18n.tr("network.join")
                                enabled: !NetworkInfo.busy && hiddenSsid.text.trim() !== "" && (!root.hiddenSecure || hiddenPassword.text.length >= 8)
                                onClicked: if (enabled) {
                                    root.error = "";
                                    NetworkInfo.joinHidden(root.hiddenDevice.name, hiddenSsid.text.trim(), root.hiddenSecure ? hiddenPassword.text : "");
                                    hiddenPassword.clear();
                                }
                            }
                            ActionButton {
                                text: I18n.tr("common.cancel")
                                enabled: !NetworkInfo.joining
                                onClicked: root.cancelHidden()
                            }
                        }
                    }
                    Text {
                        visible: root.detailsNetwork === null && Networking.devices.values.length === 0
                        text: I18n.tr("network.noDevices")
                        color: Theme.muted
                    }
                    ColumnLayout {
                        visible: root.detailsNetwork === null && root.passwordNetwork !== null
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
                    ActionButton {
                        visible: root.detailsNetwork === null
                        Layout.fillWidth: true
                        alignLeft: true
                        text: I18n.tr("network.advancedSettings")
                        onClicked: {
                            Quickshell.execDetached({
                                command: ["nm-connection-editor"]
                            });
                            ShellState.close();
                        }
                    }
                    Text {
                        visible: root.detailsNetwork === null && (root.error !== "" || NetworkInfo.error !== "")
                        text: root.error || NetworkInfo.error
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

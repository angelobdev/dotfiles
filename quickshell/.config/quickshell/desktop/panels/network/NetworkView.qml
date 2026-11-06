import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Networking
import "../.."
import "../../components"
import "../../services"
import ".."

// Network: Wi-Fi on/off and connectivity, the networks to join with their passwords, hidden networks, the
// details of one network, VPN, hotspot and Tailscale. The Network panel of the Control Center and
// Settings → Network both show it; the header above it takes title and Back from here.
ColumnLayout {
    id: root
    // On screen: scans and polling run only then.
    property bool shown: false
    readonly property Item focusItem: search
    // The header's title and whether Back closes the details instead of leaving.
    readonly property string title: detailsNetwork?.name ?? I18n.tr("network.title")
    readonly property bool inDetails: detailsNetwork !== null
    spacing: 12
    property var passwordNetwork: null
    property var detailsNetwork: null
    // The network last asked to connect, from any page: its failure is reported even when its row is not shown
    // (the details page, or filtered out by the search).
    property var attempt: null
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
    function connectTo(network) {
        error = "";
        attempt = network;
        network.connect();
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
        pageEnter.direction = 1;
        pageEnter.restart();
        if (network.connected)
            NetworkInfo.refreshDetails(network.device?.name);
    }
    function closeDetails() {
        detailsNetwork = null;
        scroll.ScrollBar.vertical.position = 0;
        pageEnter.direction = -1;
        pageEnter.restart();
        if (!Tablet.active)
            search.forceActiveFocus();
    }
    // Shown again: an empty search, fresh details. Hidden: no prompt or page left half done.
    function opened() {
        search.clear();
        // In tablet mode the search field waits for a tap: focused, it would open the keyboard just to browse.
        if (!Tablet.active)
            search.forceActiveFocus();
        NetworkInfo.refreshDetails(activeDevice?.name);
        NetworkInfo.refreshExtras();
    }
    onShownChanged: shown ? opened() : closed()
    Component.onCompleted: if (shown)
        opened()
    function closed() {
        cancelPassword();
        cancelHidden();
        hotspotSection.reset();
        detailsNetwork = null;
        error = "";
    }
    onActiveNetworkChanged: if (shown)
        NetworkInfo.refreshDetails(activeDevice?.name)
    Connections {
        target: root.attempt
        function onConnectionFailed(reason) {
            root.error = I18n.tr("network.connectionFailed", [I18n.networkDescription(ConnectionFailReason.toString(reason))]);
            // A saved password that no longer works: ask for a new one on the list page, where the prompt is.
            if (root.personal(root.attempt) && reason === ConnectionFailReason.NoSecrets) {
                const network = root.attempt;
                if (root.detailsNetwork)
                    root.closeDetails();
                root.askPassword(network);
            }
        }
    }
    // Esc: back from the details first; false when there is nothing to go back from.
    function goBack() {
        if (!detailsNetwork)
            return false;
        closeDetails();
        return true;
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
        running: root.shown && root.detailsNetwork === null
        repeat: true
        onTriggered: NetworkInfo.refreshExtras()
    }
    // List and details push like the Control Center sub-panels: the new page slides in from the side it comes from.
    ParallelAnimation {
        id: pageEnter
        property int direction: 1
        NumberAnimation {
            target: pageShift
            property: "x"
            from: 24 * pageEnter.direction
            to: 0
            duration: Theme.motionNormal
            easing.type: Easing.BezierSpline
            easing.bezierCurve: Theme.easeOut
        }
        NumberAnimation {
            target: page
            property: "opacity"
            from: 0
            to: 1
            duration: Theme.motionNormal
            easing.type: Easing.BezierSpline
            easing.bezierCurve: Theme.easeOut
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
                value: root.shown && Networking.wifiEnabled
            }
        }
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
            id: page
            width: parent.width
            spacing: 14
            transform: Translate {
                id: pageShift
            }
            Loader {
                active: root.detailsNetwork !== null
                visible: active
                Layout.fillWidth: true
                sourceComponent: NetworkDetails {
                    network: root.detailsNetwork
                    failure: root.error
                    onForgotten: root.closeDetails()
                    onConnectRequested: root.connectTo(root.detailsNetwork)
                }
            }
            // The list page: everything but the details of one network.
            ColumnLayout {
                visible: root.detailsNetwork === null
                Layout.fillWidth: true
                spacing: 14
                RowLayout {
                    ActionButton {
                        iconName: Networking.wifiEnabled ? "wifi" : "wifi-off"
                        text: Networking.wifiEnabled ? I18n.tr("network.wifiOn") : I18n.tr("network.wifiOff")
                        enabled: Networking.wifiHardwareEnabled
                        highlighted: Networking.wifiEnabled
                        onClicked: Networking.wifiEnabled = !Networking.wifiEnabled
                    }
                    // Wi-Fi on the left, the connectivity on the right.
                    Text {
                        text: I18n.networkDescription(NetworkConnectivity.toString(Networking.connectivity))
                        color: Theme.muted
                        font.pixelSize: Theme.textSize(11)
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignRight
                        elide: Text.ElideLeft
                    }
                }
                ColumnLayout {
                    visible: root.activeNetwork !== null
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: I18n.tr("network.currentConnection")
                        color: Theme.muted
                        font.pixelSize: Theme.textSize(11)
                    }
                    ActionButton {
                        id: currentConnection
                        Layout.fillWidth: true
                        implicitHeight: 58
                        text: root.activeNetwork?.name ?? ""
                        tooltip: I18n.tr("network.details")
                        onClicked: root.openDetails(root.activeNetwork)
                        background: Rectangle {
                            radius: Theme.corner(12)
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
                                    font.pixelSize: Theme.textSize(14)
                                    elide: Text.ElideRight
                                    textFormat: Text.PlainText
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: [(root.activeInfo?.ipv4 ?? []).map(a => a.split("/")[0])[0] ?? "", root.activeInfo?.frequency ? I18n.tr("network.band", [(root.activeInfo.frequency / 1000).toLocaleString(I18n.locale, "f", 1), root.activeInfo.channel]) : root.activeDevice?.type === DeviceType.Wired && root.activeDevice.linkSpeed > 0 ? I18n.tr("network.linkSpeedValue", [root.activeDevice.linkSpeed]) : ""].filter(part => part !== "").join(" · ")
                                    color: Theme.muted
                                    font.family: Theme.font
                                    font.pixelSize: Theme.textSize(11)
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
                            font.pixelSize: Theme.textSize(11)
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        // At most seven networks at a time; more scroll inside the list, and Other network stays
                        // right below it.
                        ListView {
                            id: networkList
                            readonly property int rowHeight: Theme.hit(36)
                            readonly property int shownRows: Math.min(count, 7)
                            Layout.fillWidth: true
                            Layout.preferredHeight: shownRows * rowHeight + Math.max(0, shownRows - 1) * spacing
                            visible: count > 0
                            spacing: 2
                            clip: true
                            interactive: count > 7
                            boundsBehavior: Flickable.StopAtBounds
                            ScrollBar.vertical: ScrollBar {
                                policy: networkList.count > 7 ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
                            }
                            // Rows follow their network: a reorder while scanning moves them instead of recreating
                            // every row, which lost the keyboard focus and a press in progress.
                            model: ScriptModel {
                                values: deviceRow.modelData.networks.values.filter(n => n.name.toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => Number(b.connected) - Number(a.connected) || (b.signalStrength ?? 0) - (a.signalStrength ?? 0) || a.name.localeCompare(b.name))
                            }
                            delegate: RowLayout {
                                id: networkRow
                                required property var modelData
                                readonly property bool secured: !deviceRow.wired && modelData.security !== WifiSecurityType.Open && modelData.security !== WifiSecurityType.Owe
                                width: networkList.width - (networkList.count > 7 ? 10 : 0)
                                height: networkList.rowHeight
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
                                            root.connectTo(networkRow.modelData);
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
                VpnSection {
                    panel: root
                }
                HotspotSection {
                    id: hotspotSection
                    panel: root
                }
                ColumnLayout {
                    visible: root.hiddenDevice !== null
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
                    visible: Networking.devices.values.length === 0
                    text: I18n.tr("network.noDevices")
                    color: Theme.muted
                }
                ColumnLayout {
                    visible: root.passwordNetwork !== null
                    Layout.fillWidth: true
                    Text {
                        text: I18n.tr("network.passwordFor", [root.passwordNetwork?.name ?? ""])
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
                                root.attempt = root.passwordNetwork;
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
                    visible: root.error !== "" || NetworkInfo.error !== ""
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

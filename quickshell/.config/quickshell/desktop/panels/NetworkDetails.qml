import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Networking
import ".."
import "../components"
import "../services"

ColumnLayout {
    id: root
    required property var network
    property bool confirmForget: false
    property bool editDns: false
    property bool editIp: false
    readonly property var device: network?.device ?? null
    readonly property bool wifi: device?.type === DeviceType.Wifi
    readonly property string uuid: network?.nmSettings?.[0]?.uuid ?? ""
    readonly property var profile: NetworkInfo.profile?.uuid === uuid ? NetworkInfo.profile : null
    readonly property var info: network?.connected ? NetworkInfo.details[device?.name] ?? null : null
    readonly property string dnsChoice: {
        if (!profile)
            return "";
        if (profile.dnsAutomatic)
            return "automatic";
        const preset = Config.dnsPresets.find(p => p.servers.length === profile.dns.length && p.servers.every(s => profile.dns.includes(s)));
        return preset ? preset.name : "custom";
    }
    readonly property string band: info?.frequency ? I18n.tr("network.band", [(info.frequency / 1000).toLocaleString(I18n.locale, "f", 1), info.channel]) : ""
    readonly property var infoRows: [[I18n.tr("network.ipAddress"), (info?.ipv4 ?? []).map(a => a.split("/")[0]).join(", ")], [I18n.tr("network.gateway"), info?.gateway ?? ""], [I18n.tr("network.dnsServers"), (info?.dns ?? []).join(", ")], [I18n.tr("network.ipv6Address"), (info?.ipv6 ?? []).map(a => a.split("/")[0]).join(", ")], [I18n.tr("network.linkSpeed"), !wifi && device?.linkSpeed > 0 ? I18n.tr("network.linkSpeedValue", [device.linkSpeed]) : ""], [I18n.tr("network.hardwareAddress"), info?.mac || device?.address || ""]].filter(row => row[1] !== "")
    signal forgotten
    function reset() {
        password.reset();
        confirmForget = false;
        editDns = false;
        editIp = false;
    }
    spacing: 16
    onUuidChanged: {
        reset();
        if (uuid !== "")
            NetworkInfo.loadProfile(uuid);
    }
    Component.onCompleted: if (uuid !== "")
        NetworkInfo.loadProfile(uuid)
    Component.onDestruction: NetworkInfo.forgetSensitive()
    Connections {
        target: NetworkInfo
        // DNS and metered changes are reapplied to the device, so its effective details change too.
        function onProfileChanged() {
            if (root.network?.connected)
                NetworkInfo.refreshDetails(root.device?.name);
        }
    }
    Text {
        Layout.fillWidth: true
        text: root.network?.connected ? [I18n.tr("network.status.connected"), root.wifi ? I18n.tr("network.signal", [Math.round((root.network?.signalStrength ?? 0) * 100)]) : "", root.band].filter(part => part !== "").join(" · ") : I18n.networkDescription(ConnectionState.toString(root.network?.state ?? ConnectionState.Unknown))
        color: Theme.muted
        font.pixelSize: 12
        elide: Text.ElideRight
    }
    NetworkPassword {
        id: password
        visible: root.wifi && (root.profile?.personal ?? false)
        Layout.fillWidth: true
        uuid: root.uuid
        name: root.network?.name ?? ""
    }
    ColumnLayout {
        visible: root.profile !== null
        Layout.fillWidth: true
        spacing: 4
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: I18n.tr("network.autoJoin")
                color: Theme.text
                font.pixelSize: 13
            }
            ControlSwitch {
                enabled: !NetworkInfo.busy
                onToggled: NetworkInfo.run("set", [root.uuid, "autoconnect", checked ? "yes" : "no"])
                Accessible.name: I18n.tr("network.autoJoin")
                // Re-sync with the saved profile once the helper has answered (or failed).
                Binding on checked {
                    value: root.profile?.autoconnect ?? false
                    when: !NetworkInfo.busy
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: I18n.tr("network.metered")
                color: Theme.text
                font.pixelSize: 13
            }
            ControlSwitch {
                enabled: !NetworkInfo.busy
                onToggled: NetworkInfo.run("set", [root.uuid, "metered", checked ? "yes" : "no"])
                Accessible.name: I18n.tr("network.metered")
                Binding on checked {
                    value: root.profile?.metered ?? false
                    when: !NetworkInfo.busy
                }
            }
        }
    }
    ColumnLayout {
        visible: root.profile !== null
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: I18n.tr("network.ipConfig")
            color: Theme.muted
            font.pixelSize: 11
        }
        ChoiceChips {
            enabled: !NetworkInfo.busy
            options: [
                {
                    name: "auto",
                    label: I18n.tr("network.ipAutomatic")
                },
                {
                    name: "manual",
                    label: I18n.tr("network.ipManual")
                }
            ]
            current: root.editIp || root.profile?.ipv4Method === "manual" ? "manual" : "auto"
            onChosen: name => {
                if (name === "manual") {
                    // Start from the current lease, the usual way to pin an address.
                    root.editIp = true;
                    addressField.text = root.profile.ipv4Address || ((root.info?.ipv4 ?? [])[0] ?? "");
                    gatewayField.text = root.profile.ipv4Gateway || (root.info?.gateway ?? "");
                    addressField.forceActiveFocus();
                    return;
                }
                root.editIp = false;
                if (root.profile.ipv4Method === "manual")
                    NetworkInfo.run("set-ipv4", [root.uuid, "auto"]);
            }
        }
        ColumnLayout {
            visible: root.editIp || root.profile?.ipv4Method === "manual"
            Layout.fillWidth: true
            spacing: 6
            InputField {
                id: addressField
                // Addresses: the on-screen keyboard opens on its numbers page (letters for IPv6 one tap away).
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                Layout.fillWidth: true
                implicitHeight: Theme.hit(36)
                font.pixelSize: 13
                placeholderText: I18n.tr("network.addressPlaceholder")
                text: root.profile?.ipv4Address ?? ""
                onAccepted: gatewayField.forceActiveFocus()
            }
            RowLayout {
                Layout.fillWidth: true
                InputField {
                    id: gatewayField
                // Addresses: the on-screen keyboard opens on its numbers page (letters for IPv6 one tap away).
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                    Layout.fillWidth: true
                    implicitHeight: Theme.hit(36)
                    font.pixelSize: 13
                    placeholderText: I18n.tr("network.gatewayPlaceholder")
                    text: root.profile?.ipv4Gateway ?? ""
                    onAccepted: applyIp.clicked()
                }
                ActionButton {
                    id: applyIp
                    text: I18n.tr("network.apply")
                    enabled: !NetworkInfo.busy && addressField.text.trim() !== ""
                    onClicked: if (enabled) {
                        root.editIp = false;
                        NetworkInfo.run("set-ipv4", [root.uuid, "manual", addressField.text.trim(), gatewayField.text.trim()]);
                    }
                }
            }
            Text {
                visible: root.profile?.dnsAutomatic ?? false
                Layout.fillWidth: true
                text: I18n.tr("network.manualDnsHint")
                color: Theme.muted
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }
        }
    }
    ColumnLayout {
        visible: root.profile !== null
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: I18n.tr("network.dns")
            color: Theme.muted
            font.pixelSize: 11
        }
        ChoiceChips {
            enabled: !NetworkInfo.busy
            options: [
                {
                    name: "automatic",
                    label: I18n.tr("network.dnsAutomatic")
                }
            ].concat(Config.dnsPresets.map(preset => ({
                        name: preset.name,
                        label: preset.name
                    }))).concat([
                {
                    name: "custom",
                    label: I18n.tr("network.dnsCustom")
                }
            ])
            current: root.editDns ? "custom" : root.dnsChoice
            onChosen: name => {
                if (name === "custom") {
                    root.editDns = true;
                    dnsField.text = root.dnsChoice === "custom" ? root.profile.dns.join(" ") : "";
                    dnsField.forceActiveFocus();
                    return;
                }
                root.editDns = false;
                NetworkInfo.run("set-dns", [root.uuid].concat(name === "automatic" ? [] : Config.dnsPresets.find(preset => preset.name === name).servers));
            }
        }
        RowLayout {
            visible: root.editDns || root.dnsChoice === "custom"
            Layout.fillWidth: true
            InputField {
                id: dnsField
                // Addresses: the on-screen keyboard opens on its numbers page (letters for IPv6 one tap away).
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                Layout.fillWidth: true
                implicitHeight: Theme.hit(36)
                font.pixelSize: 13
                placeholderText: I18n.tr("network.dnsCustomPlaceholder")
                text: root.dnsChoice === "custom" ? root.profile.dns.join(" ") : ""
                onAccepted: applyDns.clicked()
            }
            ActionButton {
                id: applyDns
                text: I18n.tr("network.apply")
                enabled: !NetworkInfo.busy && dnsField.text.trim() !== ""
                onClicked: if (enabled) {
                    root.editDns = false;
                    NetworkInfo.run("set-dns", [root.uuid].concat(dnsField.text.split(/[\s,]+/).filter(server => server !== "")));
                }
            }
        }
    }
    ColumnLayout {
        visible: (root.profile?.mac ?? "") !== ""
        Layout.fillWidth: true
        spacing: 8
        Text {
            text: root.wifi ? I18n.tr("network.mac") : I18n.tr("network.macWired")
            color: Theme.muted
            font.pixelSize: 11
        }
        ChoiceChips {
            enabled: !NetworkInfo.busy
            options: [
                {
                    name: "default",
                    label: I18n.tr("network.macDefault")
                },
                {
                    name: "private",
                    label: I18n.tr("network.macPrivate")
                },
                {
                    name: "rotating",
                    label: I18n.tr("network.macRotating")
                },
                {
                    name: "fixed",
                    label: I18n.tr("network.macFixed")
                }
            ]
            current: root.profile?.mac ?? ""
            onChosen: name => {
                if (name !== root.profile.mac)
                    NetworkInfo.run("set-mac", [root.uuid, name]);
            }
        }
        Text {
            Layout.fillWidth: true
            text: I18n.tr("network.macHint")
            color: Theme.muted
            font.pixelSize: 11
            wrapMode: Text.Wrap
        }
    }
    ColumnLayout {
        visible: root.infoRows.length > 0
        Layout.fillWidth: true
        spacing: 6
        Text {
            text: I18n.tr("network.info")
            color: Theme.muted
            font.pixelSize: 11
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            columnSpacing: 12
            rowSpacing: 6
            Repeater {
                model: root.infoRows.length * 2
                Text {
                    required property int index
                    readonly property var row: root.infoRows[Math.floor(index / 2)]
                    Layout.fillWidth: index % 2 === 1
                    Layout.alignment: Qt.AlignTop
                    text: row[index % 2]
                    color: index % 2 === 0 ? Theme.muted : Theme.text
                    font.pixelSize: 12
                    wrapMode: index % 2 === 1 ? Text.WrapAnywhere : Text.NoWrap
                    textFormat: Text.PlainText
                }
            }
        }
    }
    Text {
        visible: NetworkInfo.error !== ""
        Layout.fillWidth: true
        text: NetworkInfo.error
        color: Theme.danger
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ActionButton {
            text: root.network?.connected ? I18n.tr("network.disconnect") : I18n.tr("network.connect")
            enabled: !(root.network?.stateChanging ?? true)
            onClicked: {
                if (root.network.connected)
                    root.network.disconnect();
                else
                    root.network.connect();
            }
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            visible: root.network?.known ?? false
            destructive: true
            text: root.confirmForget ? I18n.tr("network.forgetConfirm") : I18n.tr("network.forget")
            onClicked: {
                if (!root.confirmForget) {
                    root.confirmForget = true;
                    return;
                }
                root.network.forget();
                root.forgotten();
            }
        }
    }
    ActionButton {
        visible: root.uuid !== ""
        Layout.fillWidth: true
        alignLeft: true
        text: I18n.tr("network.editAdvanced")
        onClicked: {
            Quickshell.execDetached({
                command: ["nm-connection-editor", "--edit=" + root.uuid]
            });
            ShellState.close();
        }
    }
}

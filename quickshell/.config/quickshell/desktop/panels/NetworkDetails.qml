import QtQuick
import QtQuick.Layouts
import Quickshell.Networking
import ".."
import "../components"
import "../services"

ColumnLayout {
    id: root
    required property var network
    property bool revealed: false
    property bool showQr: false
    property bool confirmForget: false
    property bool editDns: false
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
        revealed = false;
        showQr = false;
        confirmForget = false;
        editDns = false;
        NetworkInfo.forgetSensitive();
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
    ColumnLayout {
        visible: root.wifi && (root.profile?.personal ?? false)
        Layout.fillWidth: true
        spacing: 6
        Text {
            text: I18n.tr("network.password")
            color: Theme.muted
            font.pixelSize: 11
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                Layout.fillWidth: true
                text: root.revealed && NetworkInfo.secret !== "" ? NetworkInfo.secret : "••••••••••••"
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 14
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            CompactIconButton {
                iconName: root.revealed ? "eye-off" : "eye"
                iconSize: 18
                tooltip: root.revealed ? I18n.tr("network.hidePassword") : I18n.tr("network.showPassword")
                onClicked: {
                    root.revealed = !root.revealed;
                    if (root.revealed)
                        NetworkInfo.run("secret", [root.uuid]);
                    else
                        NetworkInfo.secret = "";
                }
            }
            CompactIconButton {
                iconName: "copy"
                iconSize: 18
                tooltip: I18n.tr("network.copyPassword")
                onClicked: NetworkInfo.run("copy-secret", [root.uuid])
            }
            CompactIconButton {
                iconName: "qr-code"
                iconSize: 18
                highlighted: root.showQr
                tooltip: I18n.tr("network.shareQr")
                onClicked: {
                    root.showQr = !root.showQr;
                    if (root.showQr)
                        NetworkInfo.run("qr", [root.uuid]);
                    else
                        NetworkInfo.qr = null;
                }
            }
        }
        Text {
            visible: NetworkInfo.copied
            text: I18n.tr("network.copied", [NetworkInfo.clearAfter])
            color: Theme.muted
            font.pixelSize: 11
        }
        Rectangle {
            visible: root.showQr && NetworkInfo.qr !== null
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 6
            implicitWidth: 196
            implicitHeight: 196
            radius: 12
            // Scanners need dark modules on a light background regardless of the theme.
            color: Theme.text
            Canvas {
                id: qrCanvas
                readonly property var code: NetworkInfo.qr
                anchors.fill: parent
                onCodeChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d");
                    context.reset();
                    if (!code)
                        return;
                    // Keep a quiet zone of about four modules and whole-pixel modules for crisp edges.
                    const cell = Math.floor(width / (code.size + 8));
                    const offset = Math.floor((width - cell * code.size) / 2);
                    context.fillStyle = String(Theme.accentText);
                    for (let y = 0; y < code.size; y++) {
                        for (let x = 0; x < code.size; x++) {
                            if (code.rows[y][x] === "1")
                                context.fillRect(offset + x * cell, offset + y * cell, cell, cell);
                        }
                    }
                }
            }
        }
        Text {
            visible: root.showQr && NetworkInfo.qr !== null
            Layout.fillWidth: true
            text: I18n.tr("network.qrHint", [root.network?.name ?? ""])
            color: Theme.muted
            font.pixelSize: 11
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
        }
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
            text: I18n.tr("network.dns")
            color: Theme.muted
            font.pixelSize: 11
        }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: [
                    {
                        name: "automatic",
                        label: I18n.tr("network.dnsAutomatic"),
                        servers: []
                    }
                ].concat(Config.dnsPresets.map(preset => ({
                            name: preset.name,
                            label: preset.name,
                            servers: preset.servers
                        }))).concat([
                    {
                        name: "custom",
                        label: I18n.tr("network.dnsCustom"),
                        servers: null
                    }
                ])
                ActionButton {
                    id: dnsOption
                    required property var modelData
                    implicitHeight: 30
                    text: modelData.label
                    font.pixelSize: 12
                    enabled: !NetworkInfo.busy
                    highlighted: root.editDns ? modelData.name === "custom" : root.dnsChoice === modelData.name
                    background: Rectangle {
                        radius: 15
                        color: dnsOption.highlighted ? Theme.accent : dnsOption.down || dnsOption.hovered || dnsOption.activeFocus ? Theme.raised : Theme.tile
                    }
                    onClicked: {
                        if (modelData.servers === null) {
                            root.editDns = true;
                            dnsField.text = root.dnsChoice === "custom" ? root.profile.dns.join(" ") : "";
                            dnsField.forceActiveFocus();
                            return;
                        }
                        root.editDns = false;
                        NetworkInfo.run("set-dns", [root.uuid].concat(modelData.servers));
                    }
                }
            }
        }
        RowLayout {
            visible: root.editDns || root.dnsChoice === "custom"
            Layout.fillWidth: true
            InputField {
                id: dnsField
                Layout.fillWidth: true
                implicitHeight: 36
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
}

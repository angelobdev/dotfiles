import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// Saved Wi-Fi password with reveal, copy and QR sharing; the secret only lives in NetworkInfo while shown.
ColumnLayout {
    id: root
    required property string uuid
    property string name: ""
    property bool revealed: false
    property bool showQr: false
    function reset() {
        revealed = false;
        showQr = false;
        NetworkInfo.forgetSensitive();
    }
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
        text: I18n.tr("network.qrHint", [root.name])
        color: Theme.muted
        font.pixelSize: 11
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.Wrap
        textFormat: Text.PlainText
    }
}

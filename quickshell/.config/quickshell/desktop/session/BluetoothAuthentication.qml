import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Bluetooth
import ".."
import "../components"
import "../services"

PanelWindow {
    id: root
    readonly property var prompt: BluetoothAgent.prompt
    readonly property var device: Bluetooth.devices.values.find(d => d.dbusPath === prompt?.device)
    readonly property bool inputRequired: ["RequestPinCode", "RequestPasskey"].includes(prompt?.kind)
    readonly property bool displayOnly: ["DisplayPinCode", "DisplayPasskey"].includes(prompt?.kind)
    readonly property bool valid: prompt?.kind === "RequestPasskey" ? /^[0-9]{1,6}$/.test(response.text) : response.text.length > 0 && response.text.length <= 16
    visible: prompt !== null
    screen: ShellState.activeScreen || Quickshell.screens[0]
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "#99000000"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-bluetooth-auth"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    onPromptChanged: {
        response.clear();
        if (prompt)
            Qt.callLater(() => inputRequired ? response.forceActiveFocus() : reject.forceActiveFocus());
    }
    contentItem.Keys.onEscapePressed: BluetoothAgent.reply(false)
    Card {
        anchors.centerIn: parent
        width: Math.min(460, parent.width - 48)
        height: content.implicitHeight + 40
        ColumnLayout {
            id: content
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                margins: 20
            }
            spacing: 12
            Heading {
                text: I18n.tr("bluetooth.pairingTitle")
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
                text: root.device?.name || root.prompt?.device || ""
                color: Theme.text
                font.bold: true
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
                text: ({
                        RequestPinCode: I18n.tr("bluetooth.enterPin"),
                        RequestPasskey: I18n.tr("bluetooth.enterPasskey"),
                        RequestConfirmation: I18n.tr("bluetooth.confirmPasskey"),
                        DisplayPinCode: I18n.tr("bluetooth.enterPinOnDevice"),
                        DisplayPasskey: I18n.tr("bluetooth.enterPasskeyOnDevice"),
                        RequestAuthorization: I18n.tr("bluetooth.confirmPairing"),
                        AuthorizeService: I18n.tr("bluetooth.authorizeService")
                    })[root.prompt?.kind] || ""
                color: Theme.text
            }
            Text {
                visible: ["RequestConfirmation", "DisplayPasskey", "DisplayPinCode"].includes(root.prompt?.kind)
                text: root.prompt?.kind === "DisplayPinCode" ? String(root.prompt?.value ?? "") : String(root.prompt?.value ?? "").padStart(6, "0")
                color: Theme.text
                font.pixelSize: 30
                font.letterSpacing: 4
                Layout.alignment: Qt.AlignHCenter
                textFormat: Text.PlainText
            }
            Text {
                visible: root.prompt?.kind === "DisplayPasskey"
                text: I18n.tr("bluetooth.enteredDigitsPrefix") + (root.prompt?.entered ?? 0)
                color: Theme.muted
            }
            Text {
                visible: root.prompt?.kind === "AuthorizeService"
                text: I18n.tr("bluetooth.servicePrefix") + (root.prompt?.value ?? "")
                Layout.fillWidth: true
                wrapMode: Text.WrapAnywhere
                textFormat: Text.PlainText
                color: Theme.muted
            }
            InputField {
                id: response
                visible: root.inputRequired
                Layout.fillWidth: true
                maximumLength: root.prompt?.kind === "RequestPasskey" ? 6 : 16
                onAccepted: if (root.valid)
                    BluetoothAgent.reply(true, text)
            }
            RowLayout {
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    id: reject
                    text: I18n.tr("common.cancel")
                    onClicked: BluetoothAgent.reply(false)
                }
                ActionButton {
                    visible: !root.displayOnly
                    text: root.inputRequired ? I18n.tr("bluetooth.submit") : I18n.tr("common.confirm")
                    enabled: !root.inputRequired || root.valid
                    onClicked: BluetoothAgent.reply(true, response.text)
                }
            }
        }
    }
}

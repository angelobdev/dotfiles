import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.Polkit
import ".."
import "../components"

Scope {
    readonly property bool registered: agent.isRegistered
    PolkitAgent {
        id: agent
        onAuthenticationRequestStarted: ShellState.close()
    }
    PanelWindow {
        id: window
        visible: agent.isActive
        screen: ShellState.activeScreen || Quickshell.screens[0]
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        exclusionMode: ExclusionMode.Ignore
        color: "#bb000000"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-authentication"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        onVisibleChanged: {
            response.clear();
            if (visible)
                response.forceActiveFocus();
        }
        contentItem.Keys.onEscapePressed: agent.flow?.cancelAuthenticationRequest()
        Connections {
            target: agent.flow
            function onIsResponseRequiredChanged() {
                response.clear();
                if (agent.flow?.isResponseRequired)
                    response.forceActiveFocus();
            }
        }
        Card {
            anchors.centerIn: parent
            width: Math.min(520, parent.width - 48)
            height: content.implicitHeight + 48
            ColumnLayout {
                id: content
                anchors {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    margins: 24
                }
                spacing: 12
                Heading {
                    text: I18n.tr("Autenticazione richiesta")
                }
                Text {
                    text: agent.flow?.message ?? ""
                    color: Theme.text
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                    textFormat: Text.PlainText
                }
                Text {
                    text: agent.flow?.actionId ?? ""
                    color: Theme.muted
                    wrapMode: Text.WrapAnywhere
                    Layout.fillWidth: true
                    textFormat: Text.PlainText
                }
                Text {
                    text: agent.flow?.inputPrompt ?? ""
                    color: Theme.text
                    textFormat: Text.PlainText
                }
                InputField {
                    id: response
                    Layout.fillWidth: true
                    enabled: agent.flow?.isResponseRequired ?? false
                    echoMode: agent.flow?.responseVisible ? TextInput.Normal : TextInput.Password
                    onAccepted: if (enabled) {
                        agent.flow.submit(text);
                        clear();
                    }
                }
                Text {
                    text: agent.flow?.supplementaryMessage ?? ""
                    color: agent.flow?.supplementaryIsError ? Theme.danger : Theme.muted
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                    textFormat: Text.PlainText
                }
                RowLayout {
                    ActionButton {
                        text: I18n.tr("Autentica")
                        enabled: response.enabled
                        onClicked: {
                            agent.flow.submit(response.text);
                            response.clear();
                        }
                    }
                    ActionButton {
                        text: I18n.tr("Annulla")
                        onClicked: agent.flow?.cancelAuthenticationRequest()
                    }
                }
            }
        }
    }
}

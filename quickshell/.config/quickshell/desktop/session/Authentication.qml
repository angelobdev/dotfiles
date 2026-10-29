import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Services.Polkit
import ".."
import "../services"
import "../components"

Scope {
    id: root
    readonly property bool registered: agent.isRegistered
    function submit() {
        if (!response.enabled)
            return;
        agent.flow.submit(response.text);
        response.clear();
    }
    PolkitAgent {
        id: agent
        onAuthenticationRequestStarted: ShellState.close()
    }
    PanelWindow {
        visible: agent.isActive
        screen: ShellState.activeScreen || Quickshell.screens[0]
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        exclusionMode: ExclusionMode.Ignore
        color: Theme.scrimStrong
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-authentication"
        // On demand in tablet mode, so touches reach the on-screen keyboard (see Overlay.qml).
        WlrLayershell.keyboardFocus: Tablet.active ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.Exclusive
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
                    text: I18n.tr("authentication.title")
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
                    onAccepted: root.submit()
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
                        text: I18n.tr("authentication.authenticate")
                        enabled: response.enabled
                        onClicked: root.submit()
                    }
                    ActionButton {
                        text: I18n.tr("common.cancel")
                        onClicked: agent.flow?.cancelAuthenticationRequest()
                    }
                }
            }
        }
    }
}

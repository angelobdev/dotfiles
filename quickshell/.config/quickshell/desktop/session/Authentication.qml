import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Services.Polkit
import ".."
import "../services"
import "../components"

Scope {
    id: root
    readonly property bool registered: agent.isRegistered
    // The focused monitor when the request came, kept while it is open: the last panel may have been elsewhere.
    property var promptScreen: null
    // A polkit identity: Quickshell gives the account or group name (string), the full name when the account has one
    // (displayName), and isGroup.
    function identityLabel(identity) {
        if (!identity)
            return "";
        const name = identity.string;
        return identity.displayName && identity.displayName !== name ? identity.displayName + " (" + name + ")" : name;
    }
    // The identities as a plain array: Quickshell hands over a QList, which has no map or find.
    readonly property var identities: {
        const list = agent.flow?.identities;
        const result = [];
        for (let i = 0; i < (list?.length ?? 0); i++)
            result.push(list[i]);
        return result;
    }
    function submit() {
        if (!response.enabled)
            return;
        agent.flow.submit(response.text);
        response.clear();
    }
    // /etc/pam.d/polkit-1 as the installer writes it (scripts/privileged/polkit-1.*) asks for the password at once and
    // takes an empty answer as "the fingerprint": offered when that stack is in place and the account has a finger enrolled.
    // Not in tablet mode, where the stack skips the reader the screen covers.
    property bool fingerprint: false
    readonly property string identityUser: agent.flow?.selectedIdentity && !agent.flow.selectedIdentity.isGroup ? agent.flow.selectedIdentity.string : ""
    // The command is set here, not bound: a binding on identityUser may not have caught up yet when this handler runs,
    // and the check then asked fprintd-list about an empty name.
    onIdentityUserChanged: {
        fingerprint = false;
        if (identityUser === "")
            return;
        prints.command = ["sh", "-c", "grep -qs desktop-fingerprint-wanted /etc/pam.d/polkit-1 && fprintd-list \"$1\" 2>/dev/null", "sh", identityUser];
        prints.running = true;
    }
    function useFingerprint() {
        if (!response.enabled)
            return;
        agent.flow.submit("");
        response.clear();
    }
    Process {
        id: prints
        stdout: StdioCollector {
            onStreamFinished: root.fingerprint = /^ - #[0-9]+:/m.test(text)
        }
    }
    PolkitAgent {
        id: agent
        onAuthenticationRequestStarted: {
            root.promptScreen = ShellState.screenNamed(Hyprland.focusedMonitor?.name);
            ShellState.close();
        }
    }
    PanelWindow {
        id: prompt
        visible: agent.isActive && !Tablet.remaps(screen?.name ?? "")
        screen: root.promptScreen || Quickshell.screens[0]
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
        // Over a keyboard that is already shown, the keyboard comes back on top and keeps its touches.
        mask: Keyboard.areaVisible && Keyboard.screenName === screen?.name ? aroundKeyboard : null
        KeyboardHole {
            id: aroundKeyboard
            content: prompt.contentItem
        }
        onVisibleChanged: {
            response.clear();
            if (visible) {
                response.forceActiveFocus();
                Keyboard.raise();
            }
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
                // Whose password PAM asks for; with several administrators, which one (polkit offers the first).
                Text {
                    visible: root.identities.length === 1
                    text: I18n.tr("authentication.identity", [root.identityLabel(agent.flow?.selectedIdentity)])
                    color: Theme.muted
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                    textFormat: Text.PlainText
                }
                ChoiceChips {
                    visible: root.identities.length > 1
                    options: root.identities.map(identity => ({
                                name: identity.string,
                                label: root.identityLabel(identity)
                            }))
                    current: agent.flow?.selectedIdentity?.string ?? ""
                    onChosen: name => {
                        const identity = root.identities.find(candidate => candidate.string === name);
                        if (identity)
                            agent.flow.selectedIdentity = identity;
                    }
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
                // PAM's own messages (the fingerprint reader's among them). pam_unix says nothing about a wrong
                // password: polkit only starts the prompt again, so that is said here.
                Text {
                    readonly property bool failedQuietly: !(agent.flow?.supplementaryMessage) && (agent.flow?.failed ?? false)
                    visible: text !== ""
                    text: failedQuietly ? I18n.tr("authentication.failed") : agent.flow?.supplementaryMessage ?? ""
                    color: failedQuietly || agent.flow?.supplementaryIsError ? Theme.danger : Theme.muted
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
                        visible: root.fingerprint && !Tablet.active
                        text: I18n.tr("authentication.useFingerprint")
                        enabled: response.enabled
                        onClicked: root.useFingerprint()
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

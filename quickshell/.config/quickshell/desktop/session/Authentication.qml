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
    // /etc/pam.d/polkit-1 as the installer writes it (scripts/privileged/polkit-1.*) tries the fingerprint first
    // (desktop-fingerprint, which prints nothing) and asks for the password after it. While the reader waits, the prompt
    // says so and offers Use password: that creates the file desktop-fingerprint looks for, which stops the reader for
    // the rest of this request (a wrong password then asks again at once). Only for the account of this session, whose
    // runtime folder holds that file, and not in tablet mode, where the stack skips the reader the screen covers.
    property bool fingerprint: false
    property bool passwordChosen: false
    readonly property string identityUser: agent.flow?.selectedIdentity && !agent.flow.selectedIdentity.isGroup ? agent.flow.selectedIdentity.string : ""
    readonly property string skipFile: Quickshell.env("XDG_RUNTIME_DIR") + "/desktop-shell/polkit-password"
    readonly property bool readerWaiting: agent.isActive && fingerprint && !passwordChosen && !Tablet.active && !(agent.flow?.isResponseRequired ?? false)
    // The command is set here, not bound: a binding on identityUser may not have caught up yet when this handler runs,
    // and the check then asked fprintd-list about an empty name.
    onIdentityUserChanged: {
        fingerprint = false;
        if (identityUser === "" || identityUser !== Quickshell.env("USER"))
            return;
        prints.command = ["sh", "-c", "grep -Eqs 'desktop-fingerprint($|[[:space:]])' /etc/pam.d/polkit-1 && fprintd-list \"$1\" 2>/dev/null", "sh", identityUser];
        prints.running = true;
    }
    function usePassword() {
        passwordChosen = true;
        Quickshell.execDetached(["sh", "-c", "mkdir -p \"${1%/*}\" && : > \"$1\"", "sh", skipFile]);
    }
    // A new request starts with the reader again.
    function forgetPassword() {
        passwordChosen = false;
        Quickshell.execDetached(["rm", "-f", "--", skipFile]);
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
            root.forgetPassword();
            root.promptScreen = ShellState.screenNamed(Hyprland.focusedMonitor?.name);
            ShellState.close();
        }
        onIsActiveChanged: if (!isActive && root.passwordChosen)
            root.forgetPassword()
    }
    PanelWindow {
        id: prompt
        // Showing the window creates it, and Quickshell announces its screen again while visible is being set:
        // read directly, that re-entered the visible binding (a binding loop). A string notifies only on a change.
        readonly property string screenName: screen?.name ?? ""
        visible: agent.isActive && !Tablet.remaps(screenName)
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
                    Layout.fillWidth: true
                    visible: root.readerWaiting
                    text: I18n.tr("authentication.touchReader")
                    color: Theme.text
                    wrapMode: Text.Wrap
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
                        outlined: true
                        text: I18n.tr("authentication.authenticate")
                        enabled: response.enabled
                        onClicked: root.submit()
                    }
                    ActionButton {
                        outlined: true
                        visible: root.readerWaiting
                        text: I18n.tr("authentication.usePassword")
                        onClicked: root.usePassword()
                    }
                    ActionButton {
                        outlined: true
                        text: I18n.tr("common.cancel")
                        onClicked: agent.flow?.cancelAuthenticationRequest()
                    }
                }
            }
        }
    }
}

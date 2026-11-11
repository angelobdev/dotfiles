import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import ".."
import "../services"
import "../components"

Overlay {
    id: root
    panelName: "power"
    busy: operation.running
    dialog: true
    closeOnEscape: false
    property string pending: ""
    property string failure: ""
    property int selectedAction: 0
    readonly property var actions: [
        {
            label: I18n.tr("session.lock"),
            action: "lock",
            key: I18n.tr("session.keys.lock"),
            icon: "lock",
            confirm: false
        },
        {
            label: I18n.tr("session.suspend"),
            action: "suspend",
            key: I18n.tr("session.keys.suspend"),
            icon: "suspend",
            confirm: true
        },
        {
            label: I18n.tr("session.logout"),
            action: "logout",
            key: I18n.tr("session.keys.logout"),
            icon: "logout",
            confirm: true
        },
        {
            label: I18n.tr("session.reboot"),
            action: "reboot",
            key: I18n.tr("session.keys.reboot"),
            icon: "reboot",
            confirm: true
        },
        {
            label: I18n.tr("session.powerOff"),
            action: "poweroff",
            key: I18n.tr("session.keys.poweroff"),
            icon: "power",
            confirm: true
        }
    ]
    function focusAction(index) {
        if (pending !== "") {
            cancel.forceActiveFocus();
            return;
        }
        if (index < 0 || index >= buttons.count)
            closeButton.forceActiveFocus();
        else {
            selectedAction = index;
            buttons.itemAt(index).forceActiveFocus();
        }
    }
    function choose(index) {
        selectedAction = index;
        const action = actions[index];
        if (action.confirm) {
            pending = action.action;
            Qt.callLater(() => cancel.forceActiveFocus());
        } else
            run(action.action);
    }
    function cancelAction() {
        pending = "";
        Qt.callLater(() => focusAction(selectedAction));
    }
    // The desktop menu can open this on one action, waiting for its confirmation (ShellState "power/ask").
    onOpened: {
        pending = "";
        failure = "";
        const ask = ShellState.recall("power/ask", "");
        ShellState.remember("power/ask", "");
        const index = actions.findIndex(entry => entry.action === ask);
        if (index >= 0)
            Qt.callLater(() => choose(index));
        else
            Qt.callLater(() => focusAction(0));
    }
    // One letter per action, from the catalogs; the same as activating the row, so it still asks first.
    contentItem.Keys.onPressed: event => {
        if (pending !== "" || operation.running || event.modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier) || event.text === "")
            return;
        const index = actions.findIndex(entry => entry.key.toLowerCase() === event.text.toLowerCase());
        if (index >= 0) {
            event.accepted = true;
            choose(index);
        }
    }
    contentItem.Keys.onEscapePressed: {
        if (pending !== "")
            cancelAction();
        else
            ShellState.close();
    }
    function run(action) {
        if (operation.running)
            return;
        failure = "";
        operation.command = [Quickshell.env("HOME") + "/.local/bin/desktop-power", action];
        operation.running = true;
    }
    Process {
        id: operation
        stderr: StdioCollector {
            id: errors
        }
        onExited: (code, status) => {
            if (code === 0) {
                if (ShellState.panel === root.panelName)
                    ShellState.close();
            } else {
                root.failure = errors.text.trim() || I18n.tr("session.operationFailed", [code]);
                root.cancelAction();
            }
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogNarrow, parent.width - 48)
        height: layout.implicitHeight + 48
        ColumnLayout {
            id: layout
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.dialogPadding
            }
            spacing: 10
            Heading {
                text: I18n.tr("session.title")
            }
            Repeater {
                id: buttons
                model: root.actions
                ActionButton {
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    implicitHeight: 42
                    text: modelData.label
                    iconName: modelData.icon
                    alignLeft: true
                    enabled: !operation.running && root.pending === ""
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    Keys.onUpPressed: root.focusAction(index - 1)
                    Keys.onDownPressed: root.focusAction(index + 1)
                    Keys.onTabPressed: event => root.focusAction(index + ((event.modifiers & Qt.ShiftModifier) ? -1 : 1))
                    Keys.onBacktabPressed: root.focusAction(index - 1)
                    onClicked: root.choose(index)
                    Text {
                        anchors {
                            right: parent.right
                            rightMargin: 12
                            verticalCenter: parent.verticalCenter
                        }
                        text: modelData.key
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                    }
                }
            }
            Text {
                visible: root.pending !== ""
                text: I18n.tr("session.confirmAction")
                color: Theme.text
            }
            RowLayout {
                visible: root.pending !== ""
                ActionButton {
                    id: confirm
                    text: I18n.tr("common.confirm")
                    enabled: !operation.running
                    // The one place the danger colour belongs: the step that carries the action out.
                    destructive: true
                    outlined: true
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    Keys.onLeftPressed: cancel.forceActiveFocus()
                    Keys.onRightPressed: cancel.forceActiveFocus()
                    KeyNavigation.tab: cancel
                    KeyNavigation.backtab: cancel
                    onClicked: root.run(root.pending)
                }
                ActionButton {
                    id: cancel
                    outlined: true
                    text: I18n.tr("common.cancel")
                    enabled: !operation.running
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    Keys.onLeftPressed: confirm.forceActiveFocus()
                    Keys.onRightPressed: confirm.forceActiveFocus()
                    KeyNavigation.tab: confirm
                    KeyNavigation.backtab: confirm
                    onClicked: root.cancelAction()
                }
            }
            Text {
                visible: root.failure !== ""
                text: root.failure
                color: Theme.danger
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
            }
            ActionButton {
                id: closeButton
                outlined: true
                text: I18n.tr("common.close")
                Layout.fillWidth: true
                Keys.onReturnPressed: clicked()
                Keys.onEnterPressed: clicked()
                Keys.onUpPressed: root.focusAction(buttons.count - 1)
                Keys.onDownPressed: root.focusAction(0)
                Keys.onTabPressed: event => root.focusAction((event.modifiers & Qt.ShiftModifier) ? buttons.count - 1 : 0)
                Keys.onBacktabPressed: root.focusAction(buttons.count - 1)
                onClicked: ShellState.close()
            }
            KeyHints {
                // Keys only; a finger needs no hint to tap a button.
                visible: !Tablet.active
                hints: I18n.tr("session.navigationHint")
            }
        }
    }
}

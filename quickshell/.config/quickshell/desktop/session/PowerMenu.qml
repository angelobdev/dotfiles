import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import ".."
import "../components"

Overlay {
    id: root
    panelName: "power"
    property string pending: ""
    property string failure: ""
    property int selectedAction: 0
    readonly property var actions: [
        {
            label: I18n.tr("session.lock"),
            action: "lock",
            icon: "lock",
            confirm: false
        },
        {
            label: I18n.tr("session.suspend"),
            action: "suspend",
            icon: "suspend",
            confirm: true
        },
        {
            label: I18n.tr("session.logout"),
            action: "logout",
            icon: "logout",
            confirm: true
        },
        {
            label: I18n.tr("session.reboot"),
            action: "reboot",
            icon: "reboot",
            confirm: true
        },
        {
            label: I18n.tr("session.powerOff"),
            action: "poweroff",
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
    onOpened: {
        pending = "";
        failure = "";
        Qt.callLater(() => focusAction(0));
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
                root.failure = errors.text.trim() || I18n.tr("session.operationFailedPrefix") + code + ").";
                root.cancelAction();
            }
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 48)
        height: layout.implicitHeight + 48
        ColumnLayout {
            id: layout
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 24
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
                    destructive: ["logout", "reboot", "poweroff"].includes(modelData.action)
                    enabled: !operation.running && root.pending === ""
                    Keys.onReturnPressed: clicked()
                    Keys.onEnterPressed: clicked()
                    Keys.onUpPressed: root.focusAction(index - 1)
                    Keys.onDownPressed: root.focusAction(index + 1)
                    Keys.onTabPressed: event => root.focusAction(index + ((event.modifiers & Qt.ShiftModifier) ? -1 : 1))
                    Keys.onBacktabPressed: root.focusAction(index - 1)
                    onClicked: root.choose(index)
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
                    highlighted: true
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
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: I18n.tr("session.navigationHint")
                font.pixelSize: 11
                color: Theme.muted
            }
        }
    }
}

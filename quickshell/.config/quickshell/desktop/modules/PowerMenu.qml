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
    onOpened: { pending = ""; failure = ""; }
    function run(action) {
        failure = "";
        operation.command = [Quickshell.env("HOME") + "/.local/bin/desktop-power", action];
        operation.running = true;
    }
    Process {
        id: operation
        stderr: StdioCollector { id: errors }
        onExited: (code, status) => {
            if (code === 0) ShellState.close();
            else root.failure = errors.text.trim() || "Operazione non riuscita (" + code + ").";
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 48)
        height: layout.implicitHeight + 48
        ColumnLayout {
            id: layout
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 10
            Heading { text: "Sessione" }
            Repeater {
                model: [
                    {label: "Blocca schermo", action: "lock", icon: "lock", confirm: false},
                    {label: "Sospendi", action: "suspend", icon: "suspend", confirm: true},
                    {label: "Esci da Hyprland", action: "logout", icon: "logout", confirm: true},
                    {label: "Riavvia il computer", action: "reboot", icon: "reboot", confirm: true},
                    {label: "Spegni il computer", action: "poweroff", icon: "power", confirm: true}
                ]
                ActionButton {
                    required property var modelData
                    Layout.fillWidth: true; implicitHeight: 42
                    text: modelData.label; iconName: modelData.icon; alignLeft: true
                    destructive: ["logout", "reboot", "poweroff"].includes(modelData.action)
                    enabled: !operation.running
                    onClicked: {
                        if (modelData.confirm) root.pending = modelData.action;
                        else root.run(modelData.action);
                    }
                }
            }
            Text { visible: root.pending !== ""; text: "Confermi l’operazione?"; color: Theme.text }
            RowLayout {
                visible: root.pending !== ""
                ActionButton { text: "Conferma"; enabled: !operation.running; highlighted: true; onClicked: root.run(root.pending) }
                ActionButton { text: "Annulla"; enabled: !operation.running; onClicked: root.pending = "" }
            }
            Text {
                visible: root.failure !== ""; text: root.failure; color: Theme.danger
                Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText
            }
            ActionButton { text: "Chiudi"; Layout.fillWidth: true; onClicked: ShellState.close() }
        }
    }
}

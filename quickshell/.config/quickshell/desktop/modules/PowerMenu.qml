import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import ".."
import "../components"
Overlay {
    id: root
    panelName: "power"
    property string pending: ""
    onOpened: pending = ""
    Card {
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 48)
        height: layout.implicitHeight + 48
        ColumnLayout {
            id: layout
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
            spacing: 12
            Heading { text: "Sessione" }
            Repeater {
                model: [{label: "Esci da Hyprland", action: "logout"}, {label: "Riavvia il computer", action: "reboot"}, {label: "Spegni il computer", action: "poweroff"}]
                ActionButton { required property var modelData; Layout.fillWidth: true; text: modelData.label; destructive: true; onClicked: root.pending = modelData.action }
            }
            Text { visible: root.pending !== ""; text: "Confermi l’operazione?"; color: Theme.text }
            RowLayout {
                visible: root.pending !== ""
                ActionButton {
                    text: "Conferma"; destructive: true
                    onClicked: {
                        if (root.pending === "logout") Hyprland.dispatch("hl.dsp.exit()");
                        else Quickshell.execDetached(["systemctl", root.pending]);
                        ShellState.close();
                    }
                }
                ActionButton { text: "Annulla"; onClicked: root.pending = "" }
            }
            ActionButton { text: "Chiudi"; Layout.fillWidth: true; onClicked: ShellState.close() }
        }
    }
}

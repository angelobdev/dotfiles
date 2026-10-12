import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
Overlay {
    panelName: "notifications"
    Card {
        anchors.centerIn: parent
        width: Math.min(540, parent.width - 48)
        height: Math.min(640, parent.height - 96)
        ColumnLayout {
            anchors { fill: parent; margins: 22 }
            spacing: 14
            Heading { text: "Notifiche" }
            RowLayout {
                ActionButton { text: Notices.quiet ? "Non disturbare: sì" : "Non disturbare: no"; highlighted: Notices.quiet; onClicked: Notices.quiet = !Notices.quiet }
                ActionButton { text: "Elimina tutte"; onClicked: Notices.clear() }
            }
            ListView {
                id: list
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true; spacing: 10
                model: Notices.notifications
                delegate: Notice { required property var modelData; width: list.width; notification: modelData }
                ScrollBar.vertical: ScrollBar {}
                Text { anchors.centerIn: parent; text: "Nessuna notifica"; visible: list.count === 0; color: Theme.muted }
            }
            ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
        }
    }
}

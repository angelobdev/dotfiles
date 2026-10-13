import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

Overlay {
    panelName: "notifications"
    SidePanelCard {
        height: Math.min(600, parent.height - 76)
        ColumnLayout {
            anchors {
                fill: parent
                margins: 16
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("Notifiche")
                PanelIconButton {
                    iconName: Notices.quiet ? "bell-off" : "bell"
                    tooltip: I18n.tr("Non disturbare")
                    highlighted: Notices.quiet
                    onClicked: Notices.quiet = !Notices.quiet
                }
                PanelIconButton {
                    iconName: "trash"
                    tooltip: I18n.tr("Elimina tutte")
                    enabled: Notices.notifications.values.length > 0
                    onClicked: Notices.clear()
                }
            }
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 10
                model: Notices.notifications
                delegate: Notice {
                    required property var modelData
                    width: list.width
                    notification: modelData
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    text: I18n.tr("Nessuna notifica")
                    visible: list.count === 0
                    color: Theme.muted
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

ControlTile {
    implicitHeight: 68
    RowLayout {
        anchors {
            fill: parent
            margins: 12
        }
        Icon {
            name: Notices.quiet ? "bell-off" : "bell"
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: I18n.tr("notifications.doNotDisturb")
                font.pixelSize: 13
                color: Theme.text
            }
            Text {
                text: Notices.quiet ? I18n.tr("notifications.silenced") : I18n.tr("notifications.enabled")
                font.pixelSize: 11
                color: Theme.muted
            }
        }
        ControlSwitch {
            checked: Notices.quiet
            onToggled: Notices.quiet = checked
            Accessible.name: I18n.tr("notifications.doNotDisturb")
            palette.highlight: Theme.accent
        }
    }
}

import QtQuick
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
            name: "coffee"
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: I18n.tr("Resta attivo")
                font.pixelSize: 13
                color: Theme.text
            }
            Text {
                text: Idle.keepAwake ? I18n.tr("Inattività sospesa") : I18n.tr("Inattività automatica")
                font.pixelSize: 11
                color: Theme.muted
            }
        }
        ControlSwitch {
            checked: Idle.keepAwake
            onToggled: Idle.keepAwake = checked
            Accessible.name: I18n.tr("Resta attivo")
        }
    }
}

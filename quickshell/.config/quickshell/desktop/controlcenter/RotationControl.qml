import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// Shown only where there is an accelerometer (Controls.qml reads "available").
ControlTile {
    readonly property bool available: Tablet.available
    implicitHeight: 68
    RowLayout {
        anchors {
            fill: parent
            margins: 12
        }
        Icon {
            name: Tablet.locked ? "rotate-lock" : "rotate"
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: I18n.tr("tablet.rotationLock")
                font.pixelSize: 13
                color: Theme.text
            }
            Text {
                text: Tablet.locked ? I18n.tr("tablet.locked") : Tablet.active ? I18n.tr("tablet.rotatesAutomatically") : I18n.tr("tablet.rotatesInTablet")
                font.pixelSize: 11
                color: Theme.muted
            }
        }
        ControlSwitch {
            checked: Tablet.locked
            onToggled: Tablet.setLocked(checked)
            Accessible.name: I18n.tr("tablet.rotationLock")
        }
    }
}

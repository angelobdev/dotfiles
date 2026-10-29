import QtQuick
import QtQuick.Layouts
import ".."
import "../components"

// A switch as a full-width row (the doNotDisturb, idle and rotation modules): the alternative to the
// switches grid, with the same icon, title and status as its ToggleTile.
ControlTile {
    id: root
    property string icon: ""
    property string title: ""
    property string status: ""
    property bool checked: false
    signal toggled(bool checked)
    implicitHeight: 68
    RowLayout {
        anchors {
            fill: parent
            margins: 12
        }
        Icon {
            name: root.icon
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: root.title
                font.pixelSize: 13
                color: Theme.text
            }
            Text {
                text: root.status
                font.pixelSize: 11
                color: Theme.muted
            }
        }
        ControlSwitch {
            checked: root.checked
            onToggled: root.toggled(checked)
            Accessible.name: root.title
        }
    }
}

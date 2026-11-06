import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../power"

// Settings → Power, below the battery warnings: the power profile and the automatic Power Saver, the same view
// as the battery panel (panels/power/PowerProfileView.qml).
ColumnLayout {
    Layout.fillWidth: true
    spacing: 6
    Text {
        text: I18n.tr("battery.profile")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: profile.implicitHeight + 20
        radius: Theme.corner(12)
        color: Theme.tile
        PowerProfileView {
            id: profile
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 10
                leftMargin: 14
                rightMargin: 14
            }
        }
    }
}

import QtQuick
import "../.."
import "../../services"

// A thin line between groups of widgets.
Item {
    id: root
    property var bar
    property bool shown: true
    implicitWidth: Theme.hit(9)
    implicitHeight: Theme.hit(30)
    Rectangle {
        anchors.centerIn: parent
        width: 1
        height: Theme.hit(16)
        color: Qt.alpha(BarStyle.muted, 0.5)
    }
}

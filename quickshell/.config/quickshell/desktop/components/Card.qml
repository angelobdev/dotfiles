import QtQuick
import ".."

Rectangle {
    color: Theme.surface
    radius: Theme.radius
    border.color: Theme.frameActive
    border.width: Theme.frameWidth
    // Consume clicks in the card; the overlay backdrop handles clicks outside it.
    MouseArea {
        anchors.fill: parent
    }
}

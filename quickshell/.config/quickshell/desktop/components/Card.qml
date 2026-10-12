import QtQuick
import ".."

Rectangle {
    color: Theme.surface
    radius: Theme.radius
    border.color: Theme.stroke
    border.width: 1
    // Consume clicks in the card; the overlay backdrop handles clicks outside it.
    MouseArea {
        anchors.fill: parent
    }
}

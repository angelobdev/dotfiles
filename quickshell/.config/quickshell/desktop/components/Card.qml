import QtQuick
import ".."
Rectangle {
    color: Theme.surface
    radius: Theme.radius
    border.color: Theme.raised
    // Consume clicks in the card; the overlay backdrop handles clicks outside it.
    MouseArea { anchors.fill: parent }
}

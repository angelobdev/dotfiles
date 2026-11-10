import QtQuick
import QtQuick.Layouts
import ".."

// A group of rows on a tile, as Settings and System lay out their options: the rows go in a column, padded inside
// the card. verticalPadding sits above and below them; leftPadding and rightPadding at the sides.
Rectangle {
    id: root
    default property alias content: column.data
    property alias spacing: column.spacing
    property int verticalPadding: 12
    property int leftPadding: 14
    property int rightPadding: 14
    implicitHeight: column.implicitHeight + 2 * verticalPadding
    radius: Theme.corner(12)
    color: Theme.tile
    ColumnLayout {
        id: column
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            topMargin: root.verticalPadding
            leftMargin: root.leftPadding
            rightMargin: root.rightPadding
        }
    }
}

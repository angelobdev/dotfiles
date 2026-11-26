import QtQuick
import "../.."

// Empty room between widgets.
Item {
    id: root
    property var bar
    property bool shown: true
    implicitWidth: Theme.hit(24)
    implicitHeight: Theme.hit(30)
}

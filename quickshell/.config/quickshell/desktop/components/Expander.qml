import QtQuick
import QtQuick.Layouts
import ".."

// A collapsible column that grows and fades in instead of appearing at once.
Item {
    id: root
    property bool expanded: false
    property alias spacing: column.spacing
    default property alias content: column.data
    Layout.fillWidth: true
    implicitHeight: expanded ? column.implicitHeight : 0
    opacity: expanded ? 1 : 0
    // Out of the parent layout (and its spacing) once fully collapsed.
    visible: implicitHeight > 0
    clip: true
    Behavior on implicitHeight {
        NumberAnimation {
            duration: Theme.motionNormal
            easing.type: Easing.BezierSpline
            easing.bezierCurve: root.expanded ? Theme.easeOut : Theme.easeIn
        }
    }
    Behavior on opacity {
        NumberAnimation {
            duration: root.expanded ? Theme.motionNormal : Theme.motionFast
        }
    }
    ColumnLayout {
        id: column
        width: parent.width
    }
}

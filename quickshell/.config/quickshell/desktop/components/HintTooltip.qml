import QtQuick
import Quickshell
import ".."

PopupWindow {
    id: root
    required property Item target
    required property string text
    property bool hovered: false
    anchor.item: target
    anchor.rect.x: target.width / 2
    anchor.rect.y: target.height + 8
    anchor.rect.width: 1
    anchor.rect.height: 1
    anchor.edges: Edges.Bottom
    anchor.gravity: Edges.Bottom
    // Slide horizontally at screen edges, preserving the position below the control.
    anchor.adjustment: PopupAdjustment.SlideX
    visible: delay.running === false && hovered && text !== "" && target.visible && !!target.QsWindow.window?.visible
    implicitWidth: Math.min(360, label.implicitWidth + 25)
    implicitHeight: label.implicitHeight + 16
    color: "transparent"
    Timer {
        id: delay
        interval: 500
        running: root.hovered && root.text !== ""
    }
    Rectangle {
        anchors.fill: parent
        radius: 9
        color: Theme.tooltip
        border.color: Theme.stroke
    }
    Text {
        id: label
        anchors {
            fill: parent
            margins: 8
            leftMargin: 12
            rightMargin: 12
        }
        text: root.text
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        font.family: Theme.font
        font.pixelSize: 12
        color: Theme.text
    }
}

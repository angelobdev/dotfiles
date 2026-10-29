import QtQuick
import QtQuick.Controls
import ".."

Slider {
    id: root
    from: 0
    to: 1
    live: true
    implicitHeight: 30
    leftPadding: 8
    rightPadding: 8
    opacity: enabled ? 1 : 0.4
    background: Rectangle {
        x: root.leftPadding
        y: (root.height - height) / 2
        width: root.availableWidth
        height: 7
        radius: 4
        color: Theme.track
        Rectangle {
            width: root.visualPosition * parent.width
            height: parent.height
            radius: 4
            color: Theme.accent
        }
    }
    handle: Rectangle {
        x: root.leftPadding + root.visualPosition * (root.availableWidth - width)
        y: (root.height - height) / 2
        width: 18
        height: 18
        radius: Theme.corner(9)
        color: root.pressed ? Theme.handlePressed : Theme.text
        border.width: root.activeFocus ? 2 : 0
        border.color: Theme.handleFocus
    }
}

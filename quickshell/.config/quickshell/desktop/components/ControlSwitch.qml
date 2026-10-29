import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Switch {
    id: root
    implicitWidth: Theme.hit(40)
    implicitHeight: Theme.hit(30)
    Layout.minimumWidth: Theme.hit(40)
    Layout.maximumWidth: Theme.hit(40)
    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
    leftPadding: 0
    rightPadding: 0
    indicator: Rectangle {
        x: root.width - width
        y: (root.height - height) / 2
        width: Theme.hit(40)
        height: Theme.hit(24)
        radius: Theme.corner(Theme.hit(12))
        color: root.checked ? Theme.accent : Theme.track
        border.width: root.activeFocus ? 1 : 0
        border.color: Theme.text
        Rectangle {
            x: root.checked ? parent.width - width - 3 : 3
            y: (parent.height - height) / 2
            width: Theme.hit(18)
            height: Theme.hit(18)
            radius: Theme.corner(Theme.hit(9))
            color: root.checked ? Theme.accentText : Theme.text
            Behavior on x {
                NumberAnimation {
                    duration: Theme.motionFast
                }
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: Theme.motionFast
            }
        }
    }
    contentItem: Item {}
    opacity: enabled ? 1 : 0.45
}

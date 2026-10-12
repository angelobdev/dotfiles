import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Switch {
    id: root
    implicitWidth: 40
    implicitHeight: 30
    Layout.minimumWidth: 40
    Layout.maximumWidth: 40
    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
    leftPadding: 0
    rightPadding: 0
    indicator: Rectangle {
        x: root.width - width
        y: (root.height - height) / 2
        width: 40
        height: 24
        radius: 12
        color: root.checked ? Theme.accent : Theme.track
        border.width: root.activeFocus ? 1 : 0
        border.color: Theme.text
        Rectangle {
            x: root.checked ? parent.width - width - 3 : 3
            y: 3
            width: 18
            height: 18
            radius: 9
            color: root.checked ? Theme.accentText : Theme.text
            Behavior on x {
                NumberAnimation {
                    duration: 120
                }
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
    }
    contentItem: Item {}
    opacity: enabled ? 1 : 0.45
}

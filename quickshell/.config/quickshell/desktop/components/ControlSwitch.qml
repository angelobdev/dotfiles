import QtQuick
import QtQuick.Controls
import ".."
Switch {
    id: root
    implicitWidth: 44; implicitHeight: 30
    leftPadding: 2; rightPadding: 2
    indicator: Rectangle {
        x: root.leftPadding; y: (root.height - height) / 2
        width: 40; height: 24; radius: 12
        color: root.checked ? Theme.accent : "#805c6068"
        border.width: root.activeFocus ? 1 : 0; border.color: Theme.text
        Rectangle {
            x: root.checked ? parent.width - width - 3 : 3
            y: 3; width: 18; height: 18; radius: 9
            color: root.checked ? Theme.background : Theme.text
            Behavior on x { NumberAnimation { duration: 120 } }
        }
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    contentItem: Item {}
    opacity: enabled ? 1 : 0.45
}

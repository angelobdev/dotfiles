import QtQuick
import QtQuick.Controls
import ".."

TextField {
    id: root
    implicitHeight: Theme.hit(42)
    leftPadding: 12
    rightPadding: 12
    color: Theme.text
    placeholderTextColor: Theme.muted
    selectionColor: Theme.accent
    selectedTextColor: Theme.accentText
    font.family: Theme.font
    font.pixelSize: 14
    background: Rectangle {
        radius: Theme.corner(8)
        color: Theme.background
        border.color: root.activeFocus ? Theme.accent : Theme.raised
    }
}

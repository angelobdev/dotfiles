import QtQuick
import QtQuick.Controls
import ".."
Button {
    id: root
    property bool destructive: false
    implicitHeight: 36
    implicitWidth: Math.max(36, label.implicitWidth + 24)
    font.family: Theme.font
    font.pixelSize: 13
    opacity: enabled ? 1 : 0.45
    Accessible.name: text
    contentItem: Text {
        id: label
        text: root.text
        font: root.font
        color: root.destructive ? Theme.danger : root.highlighted ? Theme.background : Theme.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        textFormat: Text.PlainText
    }
    background: Rectangle {
        radius: 10
        color: root.highlighted ? Theme.accent : root.down ? Theme.muted : root.hovered || root.activeFocus ? Theme.raised : Theme.surface
        border.width: root.activeFocus ? 1 : 0
        border.color: Theme.accent
    }
}

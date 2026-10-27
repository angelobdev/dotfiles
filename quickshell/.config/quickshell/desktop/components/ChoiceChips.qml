import QtQuick
import QtQuick.Layouts
import ".."

// A single choice among a few options, shown as wrapping pills.
Flow {
    id: root
    // [{ name, label }]
    property var options: []
    property string current: ""
    signal chosen(string name)
    Layout.fillWidth: true
    spacing: 6
    Repeater {
        model: root.options
        ActionButton {
            id: chip
            required property var modelData
            implicitHeight: 30
            text: modelData.label
            font.pixelSize: 12
            highlighted: root.current === modelData.name
            background: Rectangle {
                radius: 15
                color: chip.highlighted ? Theme.accent : chip.down || chip.hovered || chip.activeFocus ? Theme.raised : Theme.tile
            }
            onClicked: root.chosen(modelData.name)
        }
    }
}

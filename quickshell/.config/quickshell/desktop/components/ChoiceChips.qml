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
    // The width of all pills on one line, so a layout that does not stretch this item gives it room for
    // that instead of wrapping (a Flow has no natural width, and its implicitWidth is read-only).
    readonly property real naturalWidth: {
        let width = 0;
        for (let i = 0; i < pills.count; i++)
            width += pills.itemAt(i)?.implicitWidth ?? 0;
        return width + spacing * Math.max(0, pills.count - 1);
    }
    Layout.preferredWidth: naturalWidth
    Layout.fillWidth: true
    Layout.minimumWidth: 0
    spacing: 6
    Repeater {
        id: pills
        model: root.options
        ActionButton {
            id: chip
            required property var modelData
            implicitHeight: Theme.hit(30)
            text: modelData.label
            font.pixelSize: 12
            highlighted: root.current === modelData.name
            background: Rectangle {
                radius: Theme.corner(15)
                color: chip.highlighted ? Theme.accent : chip.down || chip.hovered || chip.activeFocus ? Theme.raised : Theme.tile
            }
            onClicked: root.chosen(modelData.name)
        }
    }
}

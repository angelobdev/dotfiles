import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

// A single choice among options in a drop-down; the same interface as ChoiceChips.
ComboBox {
    id: root
    // [{ name, label }]
    property var options: []
    property string current: ""
    signal chosen(string name)
    model: options
    textRole: "label"
    valueRole: "name"
    currentIndex: options.findIndex(option => option.name === current)
    // The choice goes out only when the user makes it; currentIndex follows `current` otherwise.
    onActivated: index => {
        const name = options[index]?.name;
        if (name !== undefined && name !== current)
            chosen(name);
    }
    implicitHeight: Theme.hit(32)
    // Wide enough for the longest label, so the box does not change size with the choice.
    implicitWidth: Math.max(Theme.hit(96), longest.advanceWidth + leftPadding + rightPadding + 8)
    Layout.minimumWidth: implicitWidth
    leftPadding: 12
    rightPadding: 12 + Theme.hit(18)
    font.family: Theme.font
    font.pixelSize: Theme.textSize(12)
    opacity: enabled ? 1 : 0.45
    TextMetrics {
        id: longest
        font: root.font
        text: root.options.reduce((wide, option) => String(option.label).length > wide.length ? String(option.label) : wide, "")
    }
    background: Rectangle {
        radius: Theme.corner(10)
        color: root.down || root.hovered || root.visualFocus ? Theme.raised : Theme.tile
        border.width: root.visualFocus || root.popup.visible ? 1 : 0
        border.color: Theme.accent
    }
    contentItem: Text {
        text: root.displayText
        textFormat: Text.PlainText
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        color: Theme.text
        font: root.font
    }
    indicator: Icon {
        x: root.width - width - 10
        y: (root.height - height) / 2
        width: 14
        height: 14
        name: "chevron-down"
        color: Theme.muted
    }
    delegate: ItemDelegate {
        id: entry
        required property var modelData
        required property int index
        width: ListView.view ? ListView.view.width : root.width
        implicitHeight: Theme.hit(30)
        leftPadding: 10
        highlighted: root.highlightedIndex === index
        contentItem: Text {
            text: entry.modelData.label
            textFormat: Text.PlainText
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            color: entry.modelData.name === root.current ? Theme.accent : Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            font.bold: entry.modelData.name === root.current
        }
        background: Rectangle {
            radius: Theme.corner(7)
            color: entry.down ? Theme.track : entry.highlighted ? Theme.raised : "transparent"
        }
    }
    popup: Popup {
        y: root.height + 4
        width: Math.max(root.width, 140)
        implicitHeight: Math.min(contentItem.implicitHeight + topPadding + bottomPadding, 320)
        padding: 4
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: root.popup.visible ? root.delegateModel : null
            currentIndex: root.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
            ScrollIndicator.vertical: ScrollIndicator {}
        }
        // The menus of the shell: the window radius, a denser fill and the active frame.
        background: Rectangle {
            radius: Theme.radius
            color: Theme.tooltip
            border.width: Theme.frameWidth
            border.color: Theme.frameActive
        }
    }
}

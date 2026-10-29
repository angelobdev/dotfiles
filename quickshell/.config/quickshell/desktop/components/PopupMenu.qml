import QtQuick
import QtQuick.Layouts
import ".."

// A context menu built from plain entries: { kind: "item" | "heading" | "separator", text, icon, checked,
// destructive, enabled, keepOpen, action }. Hover and arrow keys share one selection, Enter triggers it.
Rectangle {
    id: root
    property var entries: []
    signal triggered(var entry)
    signal dismissed
    function selectable(index) {
        const entry = entries[index];
        return !!entry && (entry.kind ?? "item") === "item" && entry.enabled !== false;
    }
    function step(direction) {
        for (let i = 1; i <= entries.length; i++) {
            const index = (list.currentIndex + direction * i + entries.length * 2) % entries.length;
            if (selectable(index)) {
                list.currentIndex = index;
                return;
            }
        }
    }
    function trigger(index) {
        if (!selectable(index))
            return;
        const entry = entries[index];
        if (entry.action)
            entry.action();
        triggered(entry);
    }
    implicitWidth: 252
    implicitHeight: list.contentHeight + 12
    radius: Theme.corner(12)
    color: Theme.background
    border.width: Theme.frameWidth
    border.color: Theme.frameActive
    onEntriesChanged: list.currentIndex = -1
    Keys.onUpPressed: step(-1)
    Keys.onDownPressed: step(1)
    Keys.onTabPressed: step(1)
    Keys.onBacktabPressed: step(-1)
    Keys.onReturnPressed: trigger(list.currentIndex)
    Keys.onEnterPressed: trigger(list.currentIndex)
    Keys.onSpacePressed: trigger(list.currentIndex)
    Keys.onEscapePressed: dismissed()
    // Presses on headings, separators and padding stay inside the menu.
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
    }
    ListView {
        id: list
        anchors {
            fill: parent
            margins: 6
        }
        interactive: false
        currentIndex: -1
        model: root.entries
        delegate: Item {
            id: row
            required property var modelData
            required property int index
            readonly property string kind: modelData.kind ?? "item"
            readonly property bool current: list.currentIndex === index
            width: list.width
            height: kind === "separator" ? 9 : kind === "heading" ? 28 : 32
            opacity: modelData.enabled === false ? 0.4 : 1
            Rectangle {
                anchors.centerIn: parent
                visible: row.kind === "separator"
                width: parent.width - 12
                height: 1
                color: Theme.stroke
            }
            Rectangle {
                anchors.fill: parent
                visible: row.kind === "item"
                radius: Theme.corner(7)
                color: mouse.pressed ? Theme.track : row.current ? Theme.raised : "transparent"
            }
            RowLayout {
                anchors {
                    fill: parent
                    leftMargin: 10
                    rightMargin: 10
                }
                visible: row.kind !== "separator"
                spacing: 8
                Item {
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                    visible: row.kind === "item" && (row.modelData.checked !== undefined || !!row.modelData.icon)
                    Image {
                        anchors.fill: parent
                        visible: row.modelData.checked === undefined
                        source: row.modelData.icon ?? ""
                        sourceSize: Qt.size(32, 32)
                        fillMode: Image.PreserveAspectFit
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: row.modelData.checked !== undefined
                        text: row.modelData.checked ? "●" : ""
                        color: Theme.text
                        font.pixelSize: 9
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: row.modelData.text ?? ""
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: row.kind === "heading" ? Theme.muted : row.modelData.destructive ? Theme.danger : Theme.text
                    font.family: Theme.font
                    font.pixelSize: row.kind === "heading" ? 12 : 13
                    font.weight: row.kind === "heading" ? Font.DemiBold : Font.Normal
                }
            }
            MouseArea {
                id: mouse
                anchors.fill: parent
                enabled: row.kind === "item" && row.modelData.enabled !== false
                hoverEnabled: true
                onContainsMouseChanged: if (containsMouse)
                    list.currentIndex = row.index
                onClicked: root.trigger(row.index)
            }
        }
    }
}

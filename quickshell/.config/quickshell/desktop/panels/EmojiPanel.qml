import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// Emoji: search by name or keyword in the interface language, or browse by group; recently used first.
// Enter or a click puts the emoji into the window that was focused (copied, then pasted).
Overlay {
    id: root
    panelName: "emoji"
    dialog: true
    // -1: recently used.
    property int group: -1
    readonly property string query: search.text.trim().toLowerCase()
    readonly property var shown: query !== "" ? Emoji.emoji.filter(e => (e.n + " " + e.k).toLowerCase().includes(query)).map(e => e.e).slice(0, 400) : group === -1 ? Emoji.recent : Emoji.emoji.filter(e => e.g === group).map(e => e.e)
    readonly property var names: {
        const byEmoji = {};
        for (const e of Emoji.emoji)
            byEmoji[e.e] = e.n;
        return byEmoji;
    }
    function groupLabel(key) {
        return ({
                smileys: I18n.tr("emoji.groups.smileys"),
                people: I18n.tr("emoji.groups.people"),
                nature: I18n.tr("emoji.groups.nature"),
                food: I18n.tr("emoji.groups.food"),
                travel: I18n.tr("emoji.groups.travel"),
                activities: I18n.tr("emoji.groups.activities"),
                objects: I18n.tr("emoji.groups.objects"),
                symbols: I18n.tr("emoji.groups.symbols"),
                flags: I18n.tr("emoji.groups.flags")
            })[key] ?? key;
    }
    onOpened: {
        // A panel is a layer: the window Hyprland reports as active is still the one to paste into.
        Emoji.remember();
        Emoji.load();
        search.clear();
        group = Emoji.recent.length > 0 ? -1 : 0;
        grid.currentIndex = 0;
        if (!Tablet.active)
            search.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(560, parent.width - 32)
        height: Math.min(520, parent.height - 76)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.dialogPadding
            spacing: 12
            PanelHeader {
                title: I18n.tr("emoji.title")
                Layout.fillWidth: true
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: I18n.tr("emoji.search")
                onTextChanged: grid.currentIndex = 0
                Keys.onDownPressed: grid.currentIndex = Math.min(grid.count - 1, grid.currentIndex + grid.columns)
                Keys.onUpPressed: grid.currentIndex = Math.max(0, grid.currentIndex - grid.columns)
                Keys.onPressed: event => {
                    if (event.key === Qt.Key_Right && (search.text === "" || search.cursorPosition === search.text.length)) {
                        grid.currentIndex = Math.min(grid.count - 1, grid.currentIndex + 1);
                        event.accepted = true;
                    } else if (event.key === Qt.Key_Left && (search.text === "" || search.cursorPosition === search.text.length)) {
                        grid.currentIndex = Math.max(0, grid.currentIndex - 1);
                        event.accepted = true;
                    }
                }
                onAccepted: if (grid.count > 0)
                    Emoji.pick(root.shown[grid.currentIndex])
            }
            // Groups: recently used, then the Unicode groups, each shown by its first emoji.
            Flow {
                Layout.fillWidth: true
                visible: root.query === ""
                spacing: 4
                Repeater {
                    model: [-1].concat(Emoji.groups.map((key, index) => index))
                    ActionButton {
                        required property int modelData
                        implicitWidth: Theme.hit(36)
                        implicitHeight: Theme.hit(36)
                        compact: true
                        topPadding: 0
                        bottomPadding: 0
                        text: modelData === -1 ? "🕘" : (Emoji.emoji.find(e => e.g === modelData)?.e ?? "")
                        font.pixelSize: Theme.textSize(18)
                        font.family: "Noto Color Emoji"
                        // The emoji alone, centred in its square.
                        contentItem: Text {
                            text: parent.text
                            font: parent.font
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        highlighted: root.group === modelData
                        tooltip: modelData === -1 ? I18n.tr("emoji.recent") : root.groupLabel(Emoji.groups[modelData])
                        onClicked: {
                            root.group = modelData;
                            grid.currentIndex = 0;
                        }
                    }
                }
            }
            GridView {
                id: grid
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                readonly property int columns: Math.max(1, Math.floor(width / cellWidth))
                cellWidth: Theme.hit(46)
                cellHeight: Theme.hit(46)
                model: root.shown
                highlight: Rectangle {
                    radius: Theme.corner(10)
                    color: Theme.raised
                    border.color: Theme.accent
                    border.width: 1
                }
                highlightMoveDuration: 0
                delegate: Item {
                    required property string modelData
                    required property int index
                    width: grid.cellWidth
                    height: grid.cellHeight
                    Text {
                        anchors.centerIn: parent
                        text: parent.modelData
                        font.pixelSize: Theme.textSize(Theme.hit(26))
                        font.family: "Noto Color Emoji"
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: Emoji.pick(parent.modelData)
                    }
                    Accessible.role: Accessible.Button
                    Accessible.name: root.names[modelData] ?? modelData
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    width: parent.width - 32
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    visible: grid.count === 0
                    text: Emoji.error !== "" ? Emoji.error : root.query !== "" ? I18n.tr("emoji.noMatch") : root.group === -1 ? I18n.tr("emoji.noRecent") : I18n.tr("emoji.loading")
                    color: Theme.muted
                }
            }
            Text {
                Layout.fillWidth: true
                elide: Text.ElideRight
                text: grid.count > 0 ? (root.names[root.shown[grid.currentIndex]] ?? "") : ""
                color: Theme.muted
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
}

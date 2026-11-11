import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../../SettingsSchema.js" as Schema

// A Settings section built from SettingsSchema.js: its groups in order, one OptionRow per option. Changes are
// written to ~/.config/desktop/shell.json at once (Config.set); the shell rereads it.
ColumnLayout {
    id: root
    required property string section
    property string title: ""
    readonly property Item focusItem: scroll
    // The keyboard: up and down pick a row, Space or Enter changes it, left and right adjust it.
    readonly property var flat: Schema.forSection(section)
    property int current: 0
    property var rows: ({})
    // The option reveal() centers once more at the next frame, "" when none.
    property string revealing: ""
    // More groups of a section, below those of the schema (Keyboard: layout and shortcuts).
    default property alias extra: extraColumn.data
    // A row a section adds at the end of the card of one of its groups, by group name (Privacy → Launcher: Clear).
    property var groupRows: ({})
    spacing: 14
    function move(step) {
        current = Math.max(0, Math.min(flat.length - 1, current + step));
        const item = rows[flat[current].key];
        if (!item)
            return;
        // Scroll just enough to show the row.
        const flick = scroll.contentItem;
        const top = item.mapToItem(column, 0, 0).y - 8;
        const bottom = top + item.height + 16;
        if (top < flick.contentY)
            flick.contentY = Math.max(0, top);
        else if (bottom > flick.contentY + flick.height)
            flick.contentY = bottom - flick.height;
    }
    function currentRow() {
        return rows[flat[current]?.key] ?? null;
    }
    // An option found by the search of the sidebar (SettingsPanel): its row becomes the current one, highlighted,
    // in the middle of the view.
    function reveal(key) {
        const at = flat.findIndex(option => option.key === key);
        if (at < 0)
            return;
        current = at;
        scroll.forceActiveFocus();
        center(key);
        // A page built or shown just now places its rows with the next frame: center again once they are placed.
        revealing = key;
    }
    function center(key) {
        const item = rows[key];
        if (!item)
            return;
        const flick = scroll.contentItem;
        const middle = item.mapToItem(column, 0, 0).y + item.height / 2 - flick.height / 2;
        flick.contentY = Math.max(0, Math.min(flick.contentHeight - flick.height, middle));
    }
    // The layouts are placed before the scene is synchronized, so the row is where it will be drawn by then (it
    // is not yet right after the page was built, or in the narrow layout right after the page was shown).
    Connections {
        target: root.revealing === "" ? null : root.Window.window
        function onBeforeSynchronizing() {
            const key = root.revealing;
            root.revealing = "";
            root.center(key);
        }
    }
    Heading {
        Layout.fillWidth: true
        text: root.title
    }
    // shell.json exists but is not valid JSON: nothing is written until it is fixed or removed.
    Rectangle {
        Layout.fillWidth: true
        visible: Config.unreadable
        implicitHeight: warning.implicitHeight + 20
        radius: Theme.corner(12)
        color: Theme.tile
        Text {
            id: warning
            anchors {
                fill: parent
                margins: 10
                leftMargin: 14
            }
            text: I18n.tr("settings.unreadable", [Config.directory + "/shell.json"])
            wrapMode: Text.Wrap
            color: Theme.danger
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
    }
    ScrollView {
        id: scroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentWidth: availableWidth
        enabled: !Config.unreadable
        focusPolicy: Qt.StrongFocus
        Keys.onUpPressed: root.move(-1)
        Keys.onDownPressed: root.move(1)
        Keys.onLeftPressed: root.currentRow()?.adjust(-1)
        Keys.onRightPressed: root.currentRow()?.adjust(1)
        Keys.onSpacePressed: root.currentRow()?.activate()
        Keys.onReturnPressed: root.currentRow()?.activate()
        Keys.onEnterPressed: root.currentRow()?.activate()
        ColumnLayout {
            id: column
            width: scroll.availableWidth
            spacing: 18
            Repeater {
                model: Schema.groups(root.section)
                ColumnLayout {
                    id: group
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: I18n.tr(Schema.groupKey(group.modelData.name))
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        font.weight: Font.DemiBold
                    }
                    GroupCard {
                        Layout.fillWidth: true
                        verticalPadding: 10
                        spacing: 12
                        Repeater {
                            model: group.modelData.options
                            OptionRow {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.minimumHeight: Theme.hit(36)
                                option: modelData
                                current: scroll.activeFocus && root.flat[root.current]?.key === modelData.key
                                keyTarget: scroll
                                Component.onCompleted: root.rows[modelData.key] = this
                            }
                        }
                        Loader {
                            Layout.fillWidth: true
                            active: !!root.groupRows[group.modelData.name]
                            visible: active
                            sourceComponent: root.groupRows[group.modelData.name] ?? null
                        }
                    }
                }
            }
            ColumnLayout {
                id: extraColumn
                Layout.fillWidth: true
                spacing: 18
            }
        }
    }
    KeyHints {
        visible: !Tablet.active
        hints: I18n.tr("settings.navigationHint")
    }
}

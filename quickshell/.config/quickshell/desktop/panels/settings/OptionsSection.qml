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
    // More groups of a section, below those of the schema (Keyboard: layout and shortcuts).
    default property alias extra: extraColumn.data
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
    Text {
        Layout.fillWidth: true
        visible: !Tablet.active
        wrapMode: Text.WordWrap
        text: I18n.tr("settings.navigationHint")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
}

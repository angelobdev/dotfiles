import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// Settings → Keyboard, below the on-screen keyboard: the layout of the physical keyboard and personal
// shortcuts, written to settings.lua through HyprSettings. Empty layout: the one of the system, as before.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 18
    // Rows being edited, saved as a whole each time one is complete; a new row waits for keys and command.
    property var rows: HyprSettings.binds.map(bind => Object.assign({}, bind))
    Component.onCompleted: HyprSettings.readActive()
    Connections {
        target: HyprSettings
        function onBindsChanged() {
            root.rows = HyprSettings.binds.map(bind => Object.assign({}, bind));
        }
    }
    function saveRows() {
        HyprSettings.setBinds(rows.filter(row => HyprSettings.validKeys(row.keys ?? "") && (row.command ?? "").trim() !== "").map(row => ({
                    keys: row.keys.trim(),
                    command: row.command.trim(),
                    description: (row.description ?? "").trim()
                })));
    }
    component GroupTitle: Text {
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    component Hint: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    // Layout
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        GroupTitle {
            text: I18n.tr("settings.hypr.layoutGroup")
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: layoutRows.implicitHeight + 20
            radius: Theme.corner(12)
            color: Theme.tile
            ColumnLayout {
                id: layoutRows
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 10
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 10
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: I18n.tr("settings.hypr.layout")
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Hint {
                            text: HyprSettings.layout === "" ? I18n.tr("settings.hypr.layoutSystem", [HyprSettings.active || "—"]) : I18n.tr("settings.hypr.layoutHint")
                        }
                    }
                    InputField {
                        id: layoutField
                        implicitWidth: 120
                        text: HyprSettings.layout
                        placeholderText: HyprSettings.active
                        Accessible.name: I18n.tr("settings.hypr.layout")
                        onEditingFinished: if (text.trim() !== HyprSettings.layout && (text.trim() === "" || HyprSettings.validLayout(text.trim())))
                            HyprSettings.setKeyboard(text, variantField.text)
                    }
                    InputField {
                        id: variantField
                        implicitWidth: 120
                        text: HyprSettings.variant
                        placeholderText: I18n.tr("settings.hypr.variant")
                        enabled: layoutField.text.trim() !== ""
                        Accessible.name: I18n.tr("settings.hypr.variant")
                        onEditingFinished: if (text.trim() !== HyprSettings.variant && HyprSettings.validVariant(text.trim()))
                            HyprSettings.setKeyboard(layoutField.text, text)
                    }
                }
                Text {
                    Layout.fillWidth: true
                    visible: (layoutField.text.trim() !== "" && !HyprSettings.validLayout(layoutField.text.trim())) || !HyprSettings.validVariant(variantField.text.trim())
                    text: I18n.tr("settings.hypr.layoutInvalid")
                    color: Theme.danger
                    wrapMode: Text.WordWrap
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                }
            }
        }
    }
    // Shortcuts
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        GroupTitle {
            text: I18n.tr("settings.hypr.bindsGroup")
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: bindRows.implicitHeight + 20
            radius: Theme.corner(12)
            color: Theme.tile
            ColumnLayout {
                id: bindRows
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 10
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 8
                Hint {
                    text: I18n.tr("settings.hypr.bindsHint")
                }
                Repeater {
                    model: root.rows
                    RowLayout {
                        id: bindRow
                        required property var modelData
                        required property int index
                        readonly property bool complete: HyprSettings.validKeys(keysField.text) && commandField.text.trim() !== ""
                        Layout.fillWidth: true
                        spacing: 8
                        function edit(field, value) {
                            const next = root.rows.slice();
                            next[index] = Object.assign({}, next[index], {
                                [field]: value
                            });
                            root.rows = next;
                            root.saveRows();
                        }
                        InputField {
                            id: keysField
                            Layout.preferredWidth: 180
                            text: bindRow.modelData.keys ?? ""
                            placeholderText: "SUPER + B"
                            color: text === "" || HyprSettings.validKeys(text) ? Theme.text : Theme.danger
                            Accessible.name: I18n.tr("settings.hypr.keys")
                            onEditingFinished: if (text !== (bindRow.modelData.keys ?? ""))
                                bindRow.edit("keys", text)
                        }
                        InputField {
                            id: commandField
                            Layout.fillWidth: true
                            text: bindRow.modelData.command ?? ""
                            placeholderText: I18n.tr("settings.hypr.command")
                            Accessible.name: I18n.tr("settings.hypr.command")
                            onEditingFinished: if (text !== (bindRow.modelData.command ?? ""))
                                bindRow.edit("command", text)
                        }
                        InputField {
                            Layout.preferredWidth: 160
                            text: bindRow.modelData.description ?? ""
                            placeholderText: I18n.tr("settings.hypr.description")
                            Accessible.name: I18n.tr("settings.hypr.description")
                            onEditingFinished: if (text !== (bindRow.modelData.description ?? ""))
                                bindRow.edit("description", text)
                        }
                        PanelIconButton {
                            iconName: "trash"
                            tooltip: I18n.tr("settings.hypr.remove")
                            onClicked: {
                                const next = root.rows.slice();
                                next.splice(bindRow.index, 1);
                                root.rows = next;
                                root.saveRows();
                            }
                        }
                    }
                }
                ActionButton {
                    text: I18n.tr("settings.hypr.add")
                    onClicked: root.rows = root.rows.concat([{
                                keys: "",
                                command: "",
                                description: ""
                            }])
                }
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: HyprSettings.error !== "" || HyprSettings.skipped.length > 0
        text: HyprSettings.error !== "" ? HyprSettings.error : I18n.tr("settings.hypr.skipped", [HyprSettings.skipped.join(", ")])
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
        color: Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Io
import "../.."
import "../../components"
import "../../services"

// Settings → Keyboard, below the on-screen keyboard: the layout of the physical keyboard and personal
// shortcuts, written to settings.lua through HyprSettings. Empty layout: the one of the system, as before.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 18
    // The shortcuts being edited, one row each. A ListModel: changing a field changes that row in place, where
    // reassigning an array rebuilt every row, the one being edited included (its save never ran).
    ListModel {
        id: bindModel
    }
    // The valid rows, as HyprSettings keeps them; an unfinished row stays in the list but is not saved.
    function valid() {
        const list = [];
        for (let i = 0; i < bindModel.count; i++) {
            const row = bindModel.get(i);
            if (HyprSettings.validKeys(row.keys) && row.command.trim() !== "")
                list.push({
                    keys: row.keys.trim(),
                    command: row.command.trim(),
                    description: row.description.trim()
                });
        }
        return list;
    }
    function load() {
        bindModel.clear();
        for (const bind of HyprSettings.binds)
            bindModel.append({
                keys: bind.keys ?? "",
                command: bind.command ?? "",
                description: bind.description ?? ""
            });
    }
    function save() {
        HyprSettings.setBinds(valid());
    }
    function editRow(index, field, value) {
        bindModel.setProperty(index, field, value);
        save();
    }
    function removeRow(index) {
        bindModel.remove(index);
        save();
    }
    // Other rows on the same keys.
    function duplicates(index, keys) {
        if (!HyprSettings.validKeys(keys))
            return 0;
        const wanted = HyprSettings.combo(keys);
        let count = 0;
        for (let i = 0; i < bindModel.count; i++) {
            const other = HyprSettings.combo(bindModel.get(i).keys);
            if (i !== index && HyprSettings.validKeys(bindModel.get(i).keys) && other.mask === wanted.mask && other.key === wanted.key)
                count++;
        }
        return count;
    }
    // The layouts the system knows, read once when the page is shown (read-only).
    property var layouts: []
    // Default first, then the layouts; a layout set by hand (us,it) that is not in the list stays selectable.
    readonly property var layoutOptions: {
        const names = layouts.slice();
        if (HyprSettings.layout !== "" && !names.includes(HyprSettings.layout))
            names.unshift(HyprSettings.layout);
        return [
            {
                name: "",
                label: I18n.tr("settings.hypr.layoutDefault", [HyprSettings.active || "—"])
            }
        ].concat(names.map(name => ({
                    name: name,
                    label: name
                })));
    }
    Component.onCompleted: {
        load();
        HyprSettings.readActive();
        layoutReader.running = true;
    }
    Process {
        id: layoutReader
        command: ["localectl", "list-x11-keymap-layouts"]
        stdout: StdioCollector {
            onStreamFinished: root.layouts = text.split("\n").map(line => line.trim()).filter(line => HyprSettings.validLayout(line))
        }
    }
    // Reloaded only when shell.json says something else than these rows (a hand edit), never after a save.
    Connections {
        target: HyprSettings
        function onBindsChanged() {
            if (JSON.stringify(HyprSettings.binds) !== JSON.stringify(root.valid()))
                root.load();
        }
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
        GroupCard {
            Layout.fillWidth: true
            verticalPadding: 10
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
                ChoiceCombo {
                    visible: root.layouts.length > 0
                    options: root.layoutOptions
                    current: HyprSettings.layout
                    Accessible.name: I18n.tr("settings.hypr.layout")
                    // A variant belongs to one layout, so it is cleared with the layout.
                    onChosen: name => HyprSettings.setKeyboard(name, "")
                }
                // Without the system list (no localectl) the layout is typed, as before.
                InputField {
                    id: layoutField
                    visible: root.layouts.length === 0
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
                    enabled: HyprSettings.layout !== "" || layoutField.text.trim() !== ""
                    Accessible.name: I18n.tr("settings.hypr.variant")
                    onEditingFinished: if (text.trim() !== HyprSettings.variant && HyprSettings.validVariant(text.trim()))
                        HyprSettings.setKeyboard(layoutField.visible ? layoutField.text : HyprSettings.layout, text)
                }
            }
            Text {
                Layout.fillWidth: true
                visible: (layoutField.visible && layoutField.text.trim() !== "" && !HyprSettings.validLayout(layoutField.text.trim())) || !HyprSettings.validVariant(variantField.text.trim())
                text: I18n.tr("settings.hypr.layoutInvalid")
                color: Theme.danger
                wrapMode: Text.WordWrap
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
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
        GroupCard {
            Layout.fillWidth: true
            verticalPadding: 10
            spacing: 8
            Hint {
                text: I18n.tr("settings.hypr.bindsHint")
            }
            Repeater {
                model: bindModel
                ColumnLayout {
                    id: bindRow
                    required property int index
                    required property string keys
                    required property string command
                    required property string description
                    // What else is on these keys: Hyprland binds (the repository, hypr.lua, this list) and the
                    // other rows here.
                    readonly property var takenBy: HyprSettings.takenBy(keys, description.trim() || command.trim())
                    readonly property int twins: root.duplicates(index, keys)
                    Layout.fillWidth: true
                    spacing: 4
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        InputField {
                            Layout.preferredWidth: 180
                            text: bindRow.keys
                            placeholderText: "SUPER + B"
                            color: text === "" || HyprSettings.validKeys(text) ? Theme.text : Theme.danger
                            Accessible.name: I18n.tr("settings.hypr.keys")
                            onEditingFinished: if (text !== bindRow.keys)
                                root.editRow(bindRow.index, "keys", text)
                        }
                        InputField {
                            Layout.fillWidth: true
                            text: bindRow.command
                            placeholderText: I18n.tr("settings.hypr.command")
                            Accessible.name: I18n.tr("settings.hypr.command")
                            onEditingFinished: if (text !== bindRow.command)
                                root.editRow(bindRow.index, "command", text)
                        }
                        InputField {
                            Layout.preferredWidth: 160
                            text: bindRow.description
                            placeholderText: I18n.tr("settings.hypr.description")
                            Accessible.name: I18n.tr("settings.hypr.description")
                            onEditingFinished: if (text !== bindRow.description)
                                root.editRow(bindRow.index, "description", text)
                        }
                        PanelIconButton {
                            iconName: "trash"
                            tooltip: I18n.tr("settings.hypr.remove")
                            onClicked: root.removeRow(bindRow.index)
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: bindRow.takenBy.length > 0 || bindRow.twins > 0
                        text: bindRow.takenBy.length > 0 ? I18n.tr("settings.hypr.taken", [bindRow.takenBy.join(", ")]) : I18n.tr("settings.hypr.twice")
                        textFormat: Text.PlainText
                        wrapMode: Text.WordWrap
                        color: Theme.danger
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                }
            }
            ActionButton {
                outlined: true
                text: I18n.tr("settings.hypr.add")
                onClicked: bindModel.append({
                    keys: "",
                    command: "",
                    description: ""
                })
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

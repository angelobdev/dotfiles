import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../../SettingsSchema.js" as Schema

// One shell option of SettingsSchema.js: its label (and hint), the control its type asks for, and Reset when
// shell.json changes it. Every change goes through Config.set, which writes ~/.config/desktop/shell.json.
Item {
    id: row
    required property var option
    // The row the arrow keys are on (OptionsSection), drawn with a highlight while the section has the focus.
    property bool current: false
    // Text and time fields hand the focus back here when they are left.
    property Item keyTarget: null
    readonly property var value: Config[option.key]
    readonly property bool changed: Config.isSet(option.key)
    implicitWidth: line.implicitWidth
    implicitHeight: line.implicitHeight
    function apply(value) {
        Config.set(option.key, value, option.fallback);
    }
    // Space or Enter: a switch flips, a choice moves to the next one, a field takes the focus.
    function activate() {
        if (option.type === "bool")
            apply(value !== true);
        else if (option.type === "choice")
            adjust(1);
        else if (option.type === "text" || option.type === "time")
            control.item?.forceActiveFocus();
    }
    // Left and right: a step of a slider, the previous or next choice, a switch off or on.
    function adjust(step) {
        if (option.type === "number")
            apply(Schema.snap(option, value + step * option.step));
        else if (option.type === "choice") {
            const names = option.options.map(String);
            const at = names.indexOf(String(value));
            const next = option.options[Math.max(0, Math.min(names.length - 1, at + step))];
            apply(next);
        } else if (option.type === "bool")
            apply(step > 0);
    }
    // Behind the row, a little wider than it.
    Rectangle {
        visible: row.current
        x: -8
        y: -4
        width: row.width + 16
        height: row.height + 8
        radius: Theme.corner(8)
        color: Theme.selection
    }
    function decimals() {
        return (String(option.step ?? 1).split(".")[1] || "").length;
    }
    function shown(value) {
        const text = typeof value === "number" ? Number(value).toFixed(decimals()) : String(value);
        return option.unit ? (option.unit === "×" || option.unit === "%" ? text + option.unit : text + " " + option.unit) : text;
    }
    function choiceLabel(name) {
        if (option.assist)
            return Assist.catalog[name]?.label ?? name;
        return shown(name);
    }
    RowLayout {
        id: line
        anchors {
            left: parent.left
            right: parent.right
            verticalCenter: parent.verticalCenter
        }
        spacing: 14
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                Layout.fillWidth: true
                text: I18n.tr(Schema.labelKey(row.option))
                wrapMode: Text.WordWrap
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
            }
            Text {
                Layout.fillWidth: true
                visible: row.option.hint === true
                text: row.option.hint ? I18n.tr(Schema.hintKey(row.option)) : ""
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
        }
        ActionButton {
            visible: row.changed
            compact: true
            text: I18n.tr("settings.reset")
            tooltip: I18n.tr("settings.resetHint", [row.shown(row.option.fallback === "" ? "—" : row.option.fallback)])
            onClicked: Config.reset(row.option.key)
        }
        Loader {
            id: control
            Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
            sourceComponent: row.option.type === "bool" ? switchControl : row.option.type === "number" ? sliderControl : row.option.type === "choice" ? choiceControl : textControl
        }
    }
    Component {
        id: switchControl
        ControlSwitch {
            checked: row.value === true
            Accessible.name: I18n.tr(Schema.labelKey(row.option))
            onToggled: row.apply(checked)
        }
    }
    Component {
        id: sliderControl
        RowLayout {
            spacing: 10
            ControlSlider {
                id: slider
                Layout.preferredWidth: 220
                from: row.option.min
                to: row.option.max
                stepSize: row.option.step
                value: row.value
                Accessible.name: I18n.tr(Schema.labelKey(row.option))
                // Written once the drag ends; arrow keys write each step.
                onPressedChanged: if (!pressed)
                    row.apply(Schema.snap(row.option, value))
                onMoved: if (!pressed)
                    row.apply(Schema.snap(row.option, value))
            }
            Text {
                Layout.preferredWidth: 64
                horizontalAlignment: Text.AlignRight
                text: row.shown(Schema.snap(row.option, slider.value))
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
    Component {
        id: choiceControl
        ChoiceCombo {
            Accessible.name: I18n.tr(Schema.labelKey(row.option))
            options: row.option.options.map(name => ({
                        name: String(name),
                        label: row.choiceLabel(name)
                    }))
            current: String(row.value)
            onChosen: name => row.apply(typeof row.option.fallback === "number" ? Number(name) : name)
        }
    }
    // Text and times: written when the field is left or Enter is pressed; a time must be HH:MM.
    Component {
        id: textControl
        InputField {
            implicitWidth: row.option.type === "time" ? 90 : 220
            text: String(row.value)
            placeholderText: row.option.type === "time" ? I18n.tr("settings.timePlaceholder") : row.option.placeholder === true ? I18n.tr(Schema.placeholderKey(row.option)) : ""
            validator: RegularExpressionValidator {
                regularExpression: row.option.type === "time" ? /^([01][0-9]|2[0-3]):[0-5][0-9]$/ : /.*/
            }
            Accessible.name: I18n.tr(Schema.labelKey(row.option))
            // The shared field draws its outline in Theme.raised, which is lost on the group tile.
            background: Rectangle {
                radius: Theme.corner(8)
                color: Theme.background
                border.color: activeFocus ? Theme.accent : Theme.stroke
            }
            onEditingFinished: {
                if (acceptableInput && text.trim() !== String(row.value))
                    row.apply(text.trim());
                row.keyTarget?.forceActiveFocus();
            }
            Keys.onEscapePressed: {
                // Bound again, not assigned: a fixed text would stop following the setting (a later Reset kept it).
                text = Qt.binding(() => String(row.value));
                row.keyTarget?.forceActiveFocus();
            }
        }
    }
}

import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// A family or icon theme installed by hand, typed in and checked before it applies.
ColumnLayout {
    id: entry
    required property string kind
    required property string placeholder
    Layout.fillWidth: true
    spacing: 4
    RowLayout {
        Layout.fillWidth: true
        InputField {
            id: field
            Layout.fillWidth: true
            implicitHeight: Theme.hit(34)
            placeholderText: entry.placeholder
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            onAccepted: Theming.applyCustom(entry.kind, text)
        }
        ActionButton {
            text: I18n.tr("theming.useCustom")
            enabled: field.text.trim() !== ""
            onClicked: Theming.applyCustom(entry.kind, field.text)
        }
    }
    Text {
        Layout.fillWidth: true
        visible: Theming.customKind === entry.kind && Theming.customError !== ""
        text: Theming.customError
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        color: Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
}

import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"

// One option of the panel: its label and a drop-down of its choices.
RowLayout {
    id: setting
    property string label: ""
    property alias options: combo.options
    property alias current: combo.current
    signal chosen(string name)
    spacing: 8
    Text {
        text: setting.label
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    ChoiceCombo {
        id: combo
        Accessible.name: setting.label
        onChosen: name => setting.chosen(name)
    }
}

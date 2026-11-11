import QtQuick
import ".."

// The title of a panel or page; with section, the label above a group inside it.
Text {
    property bool section: false
    color: section ? Theme.muted : Theme.text
    font.family: Theme.font
    font.pixelSize: Theme.textSize(section ? 12 : 18)
    font.weight: section ? Font.DemiBold : Font.Bold
    textFormat: Text.PlainText
}

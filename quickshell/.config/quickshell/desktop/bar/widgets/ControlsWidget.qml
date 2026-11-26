import QtQuick
import "../.."
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    iconName: "controls"
    tooltip: I18n.tr("controlCenter.title")
    highlighted: ShellState.panel === "controls"
    tone: "state"
    onClicked: ShellState.toggle("controls", root.bar.screen)
}

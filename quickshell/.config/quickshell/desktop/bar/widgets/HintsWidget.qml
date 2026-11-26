import QtQuick
import "../.."
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    iconName: "keyboard"
    tooltip: I18n.tr("hints.tooltip")
    onClicked: ShellState.toggle("hints", root.bar.screen)
}

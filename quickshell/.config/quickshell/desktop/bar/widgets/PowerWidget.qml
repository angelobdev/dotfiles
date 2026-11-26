import QtQuick
import "../.."
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    iconName: "power"
    tooltip: I18n.tr("session.title")
    onClicked: ShellState.toggle("power", root.bar.screen)
}

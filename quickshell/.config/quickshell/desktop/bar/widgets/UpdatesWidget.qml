import QtQuick
import "../.."
import "../../services"
import ".."

// Only while updates are available (desktop-updates.timer); the panel lists them.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Updates.count > 0
    iconName: "update"
    text: Updates.count
    tooltip: I18n.tr("updates.tooltip")
    Accessible.name: I18n.tr("updates.title")
    onClicked: ShellState.toggle("updates", root.bar.screen)
}

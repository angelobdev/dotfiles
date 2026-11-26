import QtQuick
import "../.."
import "../../services"
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    iconName: Notices.quiet ? "bell-off" : "bell"
    // A focus session shows its minutes left beside the bell.
    text: Focus.active ? I18n.tr("focus.start", [Focus.minutesLeft]) : ""
    tooltip: Focus.active ? I18n.tr("focus.tooltip", [Focus.minutesLeft]) : Notices.quiet ? I18n.tr("notifications.quietTooltip") : I18n.tr("notifications.title")
    onClicked: ShellState.toggle("notifications", root.bar.screen)
}

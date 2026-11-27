import QtQuick
import "../.."
import "../../services"
import ".."

// Only while updates are available (desktop-updates.timer), or a restart is needed to finish them; the panel lists
// them and says why.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Updates.count > 0 || Updates.restartNeeded
    iconName: Updates.count === 0 ? "reboot" : "update"
    text: Updates.count > 0 ? Updates.count : ""
    tooltip: Updates.count === 0 ? I18n.tr("updates.restart.tooltip") : I18n.tr("updates.tooltip")
    Accessible.name: I18n.tr("updates.title")
    onClicked: ShellState.toggle("updates", root.bar.screen)
}

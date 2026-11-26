import QtQuick
import Quickshell
import "../.."
import "../../services"
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    // TimeZones.revision: a new time zone shows at once, not at the next minute.
    text: TimeZones.revision >= 0 ? I18n.locale.toString(clock.date, I18n.tr("bar.dateFormat") + "  " + I18n.timeFormat) : ""
    tooltip: I18n.tr("calendar.title")
    onClicked: ShellState.toggle("calendar", root.bar.screen)
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }
}

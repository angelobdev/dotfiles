import QtQuick
import Quickshell
import "../.."
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    text: I18n.locale.toString(clock.date, I18n.tr("bar.dateFormat") + "  " + I18n.timeFormat)
    tooltip: I18n.tr("calendar.title")
    onClicked: ShellState.toggle("calendar", root.bar.screen)
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }
}

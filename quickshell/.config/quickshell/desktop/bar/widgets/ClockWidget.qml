import QtQuick
import Quickshell
import "../.."
import "../../services"
import ".."
import "../ClockFormats.js" as ClockFormats

BarButton {
    id: root
    property var bar
    property bool shown: true
    // TimeZones.revision: a new time zone shows at once, not at the next minute.
    text: TimeZones.revision >= 0 ? I18n.locale.toString(clock.date, ClockFormats.format(Config.barClockFormat, I18n.tr("bar.dateFormat"), I18n.timeFormat)) : ""
    tooltip: I18n.tr("calendar.title")
    onClicked: ShellState.toggle("calendar", root.bar.screen)
    // A right click steps to the next format, saved for every bar.
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: Config.set("barClockFormat", ClockFormats.next(Config.barClockFormat), "default")
    }
    SystemClock {
        id: clock
        // Every second only for a format that shows them.
        precision: ClockFormats.needsSeconds(Config.barClockFormat) ? SystemClock.Seconds : SystemClock.Minutes
    }
}

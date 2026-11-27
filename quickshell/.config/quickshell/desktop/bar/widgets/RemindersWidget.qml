import QtQuick
import "../.."
import "../../services"
import ".."

// While a reminder is pending: the minutes to the next one; a click opens the Reminders dialog.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Reminders.next !== null
    iconName: "clock"
    text: Reminders.next ? I18n.tr("battery.durationMinutes", [Reminders.minutesLeft(Reminders.next)]) : ""
    tooltip: Reminders.next ? (Reminders.next.text || I18n.tr("reminders.untitled")) + " · " + I18n.locale.toString(new Date(Reminders.next.at), I18n.timeFormat) : I18n.tr("reminders.title")
    onClicked: ShellState.toggle("reminders", root.bar.screen)
}

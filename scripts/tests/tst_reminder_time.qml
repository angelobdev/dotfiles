import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/ReminderTime.js" as ReminderTime

TestCase {
    name: "ReminderTime"

    readonly property real now: new Date(2026, 10, 27, 14, 0, 0).getTime()

    function minutes(text) {
        return (ReminderTime.due(text, now) - now) / 60000;
    }

    function test_minutes_and_hours() {
        compare(minutes("20"), 20);
        compare(minutes("20m"), 20);
        compare(minutes("90 min"), 90);
        compare(minutes("1h30"), 90);
        compare(minutes("1 h 30 min"), 90);
        compare(minutes("2h"), 120);
        compare(minutes("2 ore"), 120);
    }

    function test_a_time_of_day_today_or_tomorrow() {
        compare(minutes("14:30"), 30);
        compare(minutes("9.05"), 19 * 60 + 5);
        // Now itself is tomorrow: a reminder is always ahead.
        compare(minutes("14:00"), 24 * 60);
    }

    function test_nothing_else() {
        verify(isNaN(ReminderTime.due("", now)));
        verify(isNaN(ReminderTime.due("tea", now)));
        verify(isNaN(ReminderTime.due("0", now)));
        verify(isNaN(ReminderTime.due("25:00", now)));
        verify(isNaN(ReminderTime.due("2000", now)));
    }

    function test_minutes_left_round_up() {
        compare(ReminderTime.minutesLeft(now + 30000, now), 1);
        compare(ReminderTime.minutesLeft(now + 60000, now), 1);
        compare(ReminderTime.minutesLeft(now - 1000, now), 0);
    }
}

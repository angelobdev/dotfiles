import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/NightShiftSchedule.js" as Schedule

TestCase {
    name: "NightShiftSchedule"

    function at(hours, minutes) {
        return new Date(2026, 9, 29, hours, minutes, 30);
    }

    function test_windowAcrossMidnight() {
        verify(Schedule.inWindow(at(20, 0), "20:00", "07:00"));
        verify(Schedule.inWindow(at(23, 59), "20:00", "07:00"));
        verify(Schedule.inWindow(at(0, 0), "20:00", "07:00"));
        verify(Schedule.inWindow(at(6, 59), "20:00", "07:00"));
        verify(!Schedule.inWindow(at(7, 0), "20:00", "07:00"));
        verify(!Schedule.inWindow(at(19, 59), "20:00", "07:00"));
    }

    function test_windowWithinOneDay() {
        verify(Schedule.inWindow(at(13, 0), "12:00", "14:00"));
        verify(!Schedule.inWindow(at(14, 0), "12:00", "14:00"));
        verify(!Schedule.inWindow(at(11, 59), "12:00", "14:00"));
    }

    function test_nextBoundary() {
        // At 22:15 the next mark is 07:00 tomorrow; at 18:00 it is 20:00 today.
        compare(Schedule.nextBoundary(at(22, 15), "20:00", "07:00"), new Date(2026, 9, 30, 7, 0, 0).getTime());
        compare(Schedule.nextBoundary(at(18, 0), "20:00", "07:00"), new Date(2026, 9, 29, 20, 0, 0).getTime());
        // Exactly on a mark, the next one is the other mark, not the same minute.
        compare(Schedule.nextBoundary(at(20, 0), "20:00", "07:00"), new Date(2026, 9, 30, 7, 0, 0).getTime());
    }

    function test_badTimesCountAsMidnight() {
        compare(Schedule.minutes("x"), 0);
        compare(Schedule.minutes("07:30"), 450);
    }
}

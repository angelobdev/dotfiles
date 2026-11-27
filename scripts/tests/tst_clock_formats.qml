import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/bar/ClockFormats.js" as ClockFormats

TestCase {
    name: "ClockFormats"

    function test_formatsFollowTheCatalogAndTheLocale() {
        compare(ClockFormats.format("default", "ddd d MMM", "HH:mm"), "ddd d MMM  HH:mm");
        compare(ClockFormats.format("time", "ddd d MMM", "h:mm AP"), "h:mm AP");
        compare(ClockFormats.format("weekday", "ddd d MMM", "HH:mm"), "dddd  HH:mm");
        compare(ClockFormats.format("iso", "ddd d MMM", "h:mm AP"), "yyyy-MM-dd  HH:mm");
        // An unknown name (a hand-edited setting) is the default.
        compare(ClockFormats.format("nonsense", "ddd d MMM", "HH:mm"), "ddd d MMM  HH:mm");
    }

    function test_secondsGoAfterTheMinutes() {
        compare(ClockFormats.format("seconds", "d MMM", "HH:mm"), "d MMM  HH:mm:ss");
        compare(ClockFormats.withSeconds("h:mm AP"), "h:mm:ss AP");
        compare(ClockFormats.withSeconds("HH:mm:ss"), "HH:mm:ss");
        verify(ClockFormats.needsSeconds("seconds"));
        verify(!ClockFormats.needsSeconds("default"));
    }

    function test_nextWalksTheRing() {
        compare(ClockFormats.next("default"), "time");
        compare(ClockFormats.next("iso"), "default");
        compare(ClockFormats.next("nonsense"), "default");
    }
}

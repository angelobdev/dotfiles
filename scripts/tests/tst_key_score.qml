import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/osk/KeyScore.js" as KeyScore

TestCase {
    name: "KeyScore"
    readonly property real reach: 13

    function key(label, distance) {
        return {
            label: label,
            distance: distance
        };
    }

    function test_withoutPredictionTheNearestWins() {
        compare(KeyScore.pick([key("a", 2), key("s", 0)], {}, reach).label, "s");
    }

    function test_aLikelyLetterTakesATouchNearItsEdge() {
        // Inside s, 5 px from the edge of a, and a is far more likely.
        compare(KeyScore.pick([key("s", 0), key("a", 5)], {
            a: 0.9,
            s: 0.01
        }, reach).label, "a");
    }

    function test_theGrowthIsBounded() {
        // Even the certain letter cannot reach further than the reach.
        compare(KeyScore.pick([key("s", 0), key("a", 14)], {
            a: 1
        }, reach).label, "s");
    }

    function test_equallyLikelyKeysKeepTheirEdges() {
        compare(KeyScore.pick([key("s", 0), key("a", 1)], {
            a: 0.3,
            s: 0.3
        }, reach).label, "s");
    }

    function test_otherKeysNeverCompete() {
        // Backspace is nearest: the likely letter beside it does not take the touch.
        compare(KeyScore.pick([key(undefined, 0), key("l", 2)], {
            l: 0.9
        }, reach).label, undefined);
        // And a letter is not lost to a key without a letter.
        compare(KeyScore.pick([key("l", 0), key(undefined, 2)], {
            l: 0.01
        }, reach).label, "l");
    }

    function test_gainIsZeroAtTheFloorAndFullAtOne() {
        compare(KeyScore.gain(KeyScore.FLOOR, reach), 0);
        compare(KeyScore.gain(0, reach), 0);
        compare(KeyScore.gain(undefined, reach), 0);
        fuzzyCompare(KeyScore.gain(1, reach), reach, 0.0001);
    }

    function test_noKeys() {
        compare(KeyScore.pick([], {
            a: 1
        }, reach), null);
    }
}

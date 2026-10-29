import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/dock/DockModel.js" as DockModel

TestCase {
    name: "DockModel"

    function test_baseOffsetIsSymmetric() {
        // Five 52 px cells, no separator: the middle one is centred and the ends mirror each other.
        compare(DockModel.baseOffset(2, 5, -1, 52, 13), 0);
        compare(DockModel.baseOffset(0, 5, -1, 52, 13), -DockModel.baseOffset(4, 5, -1, 52, 13));
    }

    function test_baseOffsetCountsTheSeparator() {
        // A separator before item 3 of 5 widens the row by 13 px and shifts items from it onward.
        const before = DockModel.baseOffset(2, 5, 3, 52, 13);
        const after = DockModel.baseOffset(3, 5, 3, 52, 13);
        compare(after - before, 52 + 13);
        compare(DockModel.baseOffset(0, 5, 3, 52, 13), -(5 * 52 + 13) / 2 + 26);
    }

    function test_magnifyPeaksUnderThePointer() {
        compare(DockModel.magnify(0, 52, 1.4), 1.4);
        verify(DockModel.magnify(52, 52, 1.4) < 1.4);
        verify(DockModel.magnify(52, 52, 1.4) > DockModel.magnify(104, 52, 1.4));
        compare(DockModel.magnify(-52, 52, 1.4), DockModel.magnify(52, 52, 1.4));
    }

    function test_magnifyFallsOffToRest() {
        compare(DockModel.magnify(52 * 2.5, 52, 1.4), 1);
        compare(DockModel.magnify(1000, 52, 1.4), 1);
        compare(DockModel.magnify(NaN, 52, 1.4), 1);
    }

    function test_dropIndexPicksNearestPinnedSlot() {
        // Seven items, four pinned, separator before item 4.
        compare(DockModel.dropIndex(DockModel.baseOffset(2, 7, 4, 52, 13), 4, 7, 4, 52, 13), 2);
        compare(DockModel.dropIndex(DockModel.baseOffset(1, 7, 4, 52, 13) + 20, 4, 7, 4, 52, 13), 1);
        // Beyond either end, the drop clamps to the first or last pinned slot.
        compare(DockModel.dropIndex(-1000, 4, 7, 4, 52, 13), 0);
        compare(DockModel.dropIndex(1000, 4, 7, 4, 52, 13), 3);
    }

    function test_dragShiftOpensTheGapAtTheTarget() {
        // Dragging slot 1 to slot 3: slots 2 and 3 move left, the dragged one moves two cells right.
        compare(DockModel.dragShift(1, 1, 3, 52), 104);
        compare(DockModel.dragShift(2, 1, 3, 52), -52);
        compare(DockModel.dragShift(3, 1, 3, 52), -52);
        compare(DockModel.dragShift(0, 1, 3, 52), 0);
        compare(DockModel.dragShift(4, 1, 3, 52), 0);
        // Dragging slot 3 to slot 0: slots 0–2 move right.
        compare(DockModel.dragShift(0, 3, 0, 52), 52);
        compare(DockModel.dragShift(2, 3, 0, 52), 52);
        compare(DockModel.dragShift(3, 3, 0, 52), -156);
        compare(DockModel.dragShift(1, -1, -1, 52), 0);
    }

    function test_magnifyOff() {
        compare(DockModel.magnify(0, 52, 1), 1);
        compare(DockModel.magnify(0, 52, undefined), 1);
    }
}

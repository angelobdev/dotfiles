import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/bar/WorkspaceModel.js" as WorkspaceModel

TestCase {
    name: "WorkspaceModel"

    function slot(id, count) {
        return { id: id, count: count, urgent: false };
    }

    function test_newIdStaysAboveTheLastSlot() {
        const slots = { "DP-1": [slot(3, 1), slot(5, 1)] };
        compare(WorkspaceModel.newId(slots, "DP-1"), 6);
    }

    function test_newIdSkipsTheWorkspacesOfOtherMonitors() {
        const slots = { "DP-1": [slot(2, 1), slot(3, 1)], "eDP-1": [slot(4, 1), slot(5, 1)] };
        compare(WorkspaceModel.newId(slots, "DP-1"), 6);
    }

    function test_newIdSkipsThePlaceholdersOfOtherMonitors() {
        const slots = WorkspaceModel.build(
            [{ id: 1, monitor: "eDP-1", count: 1, urgent: false },
             { id: 2, monitor: "DP-1", count: 1, urgent: false },
             { id: 3, monitor: "DP-1", count: 1, urgent: false }],
            [{ name: "eDP-1", activeId: 1 }, { name: "DP-1", activeId: 3 }],
            2);
        compare(slots["eDP-1"].map(w => w.id), [1, 4]);
        compare(WorkspaceModel.newId(slots, "DP-1"), 5);
    }

    function test_newIdOfAMonitorWithoutSlots() {
        compare(WorkspaceModel.newId({}, "DP-1"), 1);
    }

    function test_scrollMovesAlongTheSlots() {
        const slots = [slot(1, 1), slot(2, 0), slot(4, 1)];
        compare(WorkspaceModel.scrollTarget(slots, 1, 1, 5), 2);
        compare(WorkspaceModel.scrollTarget(slots, 4, -1, 5), 2);
    }

    function test_scrollPastAnOccupiedLastSlotOpensANewWorkspace() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 2, 1, 3), 3);
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 2, 4, 3), 3);
    }

    function test_scrollPastAnEmptyLastSlotStays() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 0)], 2, 1, 3), -1);
    }

    function test_scrollBeforeTheFirstSlotStays() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 1, -1, 3), -1);
    }

    function test_aLongScrollStopsOnTheLastSlot() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 1, 3, 3), 2);
    }

    function test_scrollFromAnUnknownWorkspaceStays() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 9, 1, 3), -1);
    }

    function test_scrollWithoutANewIdStaysOnTheLastSlot() {
        compare(WorkspaceModel.scrollTarget([slot(1, 1), slot(2, 1)], 2, 1, -1), -1);
    }
}

import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/bar/BarLayoutModel.js" as BarLayoutModel

TestCase {
    name: "BarLayoutModel"

    function known(id) {
        return ["launcher", "workspaces", "title", "clock", "power", "separator"].indexOf(id) >= 0;
    }
    function repeats(id) {
        return id === "separator";
    }
    function layout(left, center, right) {
        return {
            left: left,
            centerLeft: [],
            center: center,
            centerRight: [],
            right: right
        };
    }

    function test_normalizeFallsBackToClassic() {
        compare(BarLayoutModel.normalize(null, known, repeats), BarLayoutModel.presets.classic);
        compare(BarLayoutModel.normalize([], known, repeats), BarLayoutModel.presets.classic);
        compare(BarLayoutModel.normalize("left", known, repeats), BarLayoutModel.presets.classic);
        compare(BarLayoutModel.normalize({}, known, repeats), BarLayoutModel.presets.classic);
        // An emptied bar stays empty.
        compare(BarLayoutModel.normalize({ left: [] }, known, repeats), layout([], [], []));
    }

    function test_normalizeDropsUnknownAndDuplicates() {
        const value = {
            left: ["launcher", "nothing", 3, "clock"],
            center: ["clock", "separator", "separator"],
            right: "power",
            elsewhere: ["power"]
        };
        compare(BarLayoutModel.normalize(value, known, repeats), layout(["launcher", "clock"], ["separator", "separator"], []));
    }

    function test_classicIsTheBarBeforeLayouts() {
        const classic = BarLayoutModel.presets.classic;
        compare(classic.left, ["launcher", "workspaces", "title"]);
        compare(classic.right, ["tray", "media", "privacy", "recording", "battery", "updates", "assistant", "hints", "notifications", "controls", "clock", "power"]);
        compare(classic.centerLeft.length + classic.center.length + classic.centerRight.length, 0);
    }

    function test_moveWithinASection() {
        const start = layout(["launcher", "workspaces", "title"], [], []);
        compare(BarLayoutModel.move(start, "left", 0, "left", 3).left, ["workspaces", "title", "launcher"]);
        compare(BarLayoutModel.move(start, "left", 2, "left", 0).left, ["title", "launcher", "workspaces"]);
        // Dropping a widget on either side of itself leaves the order.
        compare(BarLayoutModel.move(start, "left", 1, "left", 1).left, start.left);
        compare(BarLayoutModel.move(start, "left", 1, "left", 2).left, start.left);
    }

    function test_moveAcrossSectionsLeavesTheSourceAlone() {
        const start = layout(["launcher", "title"], [], ["power"]);
        const moved = BarLayoutModel.move(start, "left", 1, "center", 0);
        compare(moved.left, ["launcher"]);
        compare(moved.center, ["title"]);
        compare(start.left, ["launcher", "title"]);
    }

    function test_insertAndRemove() {
        const start = layout(["launcher"], [], ["power"]);
        compare(BarLayoutModel.insert(start, "clock", "right", 0).right, ["clock", "power"]);
        compare(BarLayoutModel.insert(start, "clock", "right", 9).right, ["power", "clock"]);
        compare(BarLayoutModel.removeAt(start, "left", 0).left, []);
        verify(BarLayoutModel.equal(start, layout(["launcher"], [], ["power"])));
        verify(!BarLayoutModel.equal(start, layout([], [], ["power"])));
    }

    function test_availableKeepsRepeatingWidgets() {
        const placed = layout(["launcher", "separator"], [], []);
        compare(BarLayoutModel.available(placed, ["launcher", "clock", "separator"], repeats), ["clock", "separator"]);
    }

    function test_dropIndex() {
        compare(BarLayoutModel.dropIndex([10, 40, 70], 0), 0);
        compare(BarLayoutModel.dropIndex([10, 40, 70], 41), 2);
        compare(BarLayoutModel.dropIndex([10, 40, 70], 100), 3);
        compare(BarLayoutModel.dropIndex([], 5), 0);
    }

    function test_centerBlockStaysCentredWhileItFits() {
        compare(BarLayoutModel.centerX(1000, 200, 100, 300, 5), 400);
        // Too wide on the right: pushed left until it touches the right section.
        compare(BarLayoutModel.centerX(1000, 200, 100, 450, 5), 345);
        // Too wide on the left: pushed right past the left section.
        compare(BarLayoutModel.centerX(1000, 200, 450, 100, 5), 455);
        compare(BarLayoutModel.centerX(1000, 200, 0, 0, 5), 400);
    }
}

import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/panels/displays/MonitorMap.js" as MonitorMap

TestCase {
    name: "MonitorMap"

    function monitor(name, x, y, width, height, scale, extra) {
        return Object.assign({ name: name, id: 0, x: x, y: y, width: width, height: height, scale: scale,
                               transform: 0, disabled: false, mirrorOf: "none" }, extra ?? {});
    }

    // The laptop panel at 1.667 and a 1080p monitor to its right, as Hyprland reports them.
    function sideBySide() {
        return [monitor("eDP-1", 0, 0, 2880, 1800, 1.6666666, { id: 0 }),
                monitor("DP-1", 1728, 0, 1920, 1080, 1, { id: 1 })];
    }

    function test_logicalSizeDividesByTheScale() {
        const size = MonitorMap.logicalSize(monitor("eDP-1", 0, 0, 2880, 1800, 1.6666666));
        compare(Math.round(size.width), 1728);
        compare(Math.round(size.height), 1080);
    }

    function test_logicalSizeTurnsWithAQuarterTransform() {
        const size = MonitorMap.logicalSize(monitor("eDP-1", 0, 0, 2880, 1800, 2, { transform: 1 }));
        compare(size.width, 900);
        compare(size.height, 1440);
        compare(MonitorMap.logicalSize(monitor("eDP-1", 0, 0, 2880, 1800, 2, { transform: 2 })).width, 1440);
    }

    function test_oneMonitorFillsTheHeightCentred() {
        const boxes = MonitorMap.boxes([monitor("DP-1", 0, 0, 1920, 1080, 1)], 400, 108);
        compare(boxes.length, 1);
        compare(boxes[0].height, 108);
        compare(boxes[0].width, 192);
        compare(boxes[0].x, 104);
        compare(boxes[0].y, 0);
        compare(boxes[0].names, ["DP-1"]);
    }

    function test_sideBySideKeepsProportions() {
        const boxes = MonitorMap.boxes(sideBySide(), 400, 108);
        compare(boxes.length, 2);
        // 3648 × 1080 logical pixels fitted to the height: 0.1 per pixel, 17.6 px either side.
        compare(boxes[0].x, 18);
        compare(boxes[0].width, 172);
        compare(boxes[0].height, 108);
        // The neighbours meet on the same pixel.
        compare(boxes[1].x, boxes[0].x + boxes[0].width);
        compare(boxes[1].width, 192);
        compare(boxes[1].height, 108);
    }

    function test_fitsTheWidthWhenWide() {
        const boxes = MonitorMap.boxes(sideBySide(), 200, 200);
        compare(boxes[0].x, 0);
        compare(boxes[1].x + boxes[1].width, 200);
        verify(boxes[0].y > 0);
    }

    function test_disabledAndFallbackAreLeftOut() {
        const list = sideBySide();
        list[0].disabled = true;
        list.push(monitor("FALLBACK", 0, 0, 1920, 1080, 1));
        const boxes = MonitorMap.boxes(list, 400, 108);
        compare(boxes.length, 1);
        compare(boxes[0].names, ["DP-1"]);
    }

    function test_aMirrorJoinsTheMonitorItShows() {
        const byId = MonitorMap.boxes([monitor("DP-1", 0, 0, 1920, 1080, 1, { id: 1, mirrorOf: "0" }),
                                       monitor("eDP-1", 0, 0, 2880, 1800, 1.6666666, { id: 0 })], 400, 108);
        compare(byId.length, 1);
        compare(byId[0].names, ["eDP-1", "DP-1"]);
        // The box of the panel, not of the mirror: 1728 × 1080 logical pixels.
        compare(byId[0].height, 108);
        verify(Math.abs(byId[0].width - 173) <= 1);
        const byName = MonitorMap.boxes([monitor("eDP-1", 0, 0, 2880, 1800, 1.6666666),
                                         monitor("DP-1", 1728, 0, 1920, 1080, 1, { mirrorOf: "eDP-1" })], 400, 108);
        compare(byName.length, 1);
        compare(byName[0].names, ["eDP-1", "DP-1"]);
    }

    function test_monitorsAtTheSamePlaceShareABox() {
        const boxes = MonitorMap.boxes([monitor("eDP-1", 0, 0, 1920, 1080, 1), monitor("DP-1", 0, 0, 1920, 1080, 1)], 400, 108);
        compare(boxes.length, 1);
        compare(boxes[0].names, ["eDP-1", "DP-1"]);
    }

    function test_nothingToDraw() {
        compare(MonitorMap.boxes([], 400, 108), []);
        compare(MonitorMap.boxes(undefined, 400, 108), []);
        compare(MonitorMap.boxes(sideBySide(), 0, 108), []);
    }
}

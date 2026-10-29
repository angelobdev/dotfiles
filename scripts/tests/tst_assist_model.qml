import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/assist/AssistModel.js" as AssistModel

TestCase {
    name: "AssistModel"

    // A 1728x1080 surface with a 38 px bar, a 56 px button and 16 px margins.
    function test_placeKeepsTheButtonInsideTheFreeHeight() {
        compare(AssistModel.place({ side: "right", fraction: 0 }, 56, 1728, 1080, 38, 16, 0), { x: 1656, y: 54 });
        compare(AssistModel.place({ side: "left", fraction: 1 }, 56, 1728, 1080, 38, 16, 0), { x: 16, y: 1008 });
        compare(AssistModel.place({ side: "left", fraction: 7 }, 56, 1728, 1080, 38, 16, 0).y, 1008);
    }

    function test_tuckSlidesPastTheEdge() {
        const right = AssistModel.place({ side: "right", fraction: 0.5 }, 56, 1728, 1080, 38, 16, 0.5);
        verify(right.x + 56 > 1728);
        const left = AssistModel.place({ side: "left", fraction: 0.5 }, 56, 1728, 1080, 38, 16, 0.5);
        verify(left.x < 0);
        compare(left.y, right.y);
    }

    function test_snapPicksTheNearerSide() {
        compare(AssistModel.snap(400, 54, 56, 1728, 1080, 38, 16).side, "left");
        compare(AssistModel.snap(1300, 54, 56, 1728, 1080, 38, 16).side, "right");
        compare(AssistModel.snap(1300, 54, 56, 1728, 1080, 38, 16).fraction, 0);
        compare(AssistModel.snap(1300, -500, 56, 1728, 1080, 38, 16).fraction, 0);
        compare(AssistModel.snap(1300, 5000, 56, 1728, 1080, 38, 16).fraction, 1);
    }

    function test_snapAndPlaceRoundTrip() {
        const position = AssistModel.snap(1650, 500, 56, 1728, 1080, 38, 16);
        const placed = AssistModel.place(position, 56, 1728, 1080, 38, 16, 0);
        compare(placed.y, 500);
        // The same fraction lands proportionally on a rotated (portrait) surface.
        const portrait = AssistModel.place(position, 56, 1080, 1728, 38, 16, 0);
        verify(portrait.y > 500 && portrait.y < 1728 - 56);
    }

    function test_menuOpensTowardsTheMiddleAndStaysInside() {
        const right = AssistModel.menuOrigin({ x: 1656, y: 500 }, 56, "right", 340, 200, 1728, 1080, 38, 16, 12);
        compare(right.x, 1656 - 12 - 340);
        compare(right.y, 500 + 28 - 100);
        const left = AssistModel.menuOrigin({ x: 16, y: 1008 }, 56, "left", 340, 200, 1728, 1080, 38, 16, 12);
        compare(left.x, 16 + 56 + 12);
        compare(left.y, 1080 - 16 - 200);
        const top = AssistModel.menuOrigin({ x: 16, y: 54 }, 56, "left", 340, 200, 1728, 1080, 38, 16, 12);
        compare(top.y, 54);
    }
}

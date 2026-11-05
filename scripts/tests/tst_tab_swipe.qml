import QtQuick
import QtQuick.Controls
import QtTest
import "../../quickshell/.config/quickshell/desktop/components"

TestCase {
    id: test
    name: "TabSwipe"
    // Visible, or its items get no pointer events.
    visible: true
    when: windowShown
    width: 400
    height: 300
    property var steps: []

    Item {
        id: area
        anchors.fill: parent
        TabSwipe {
            onSwiped: step => test.steps = test.steps.concat([step])
        }
        // What the pages hold: a vertical list and a slider.
        ListView {
            id: list
            x: 0
            y: 0
            width: 200
            height: 200
            model: 50
            delegate: Rectangle {
                required property int index
                width: 200
                height: 40
            }
        }
        Slider {
            id: slider
            x: 220
            y: 250
            width: 170
            height: 40
        }
    }

    function swipe(fromX, toX, stepsCount, pause) {
        const touch = touchEvent(area);
        touch.press(0, area, fromX, 150).commit();
        for (let i = 1; i <= stepsCount; i++) {
            wait(pause);
            touch.move(0, area, fromX + (toX - fromX) * i / stepsCount, 150).commit();
        }
        touch.release(0, area, toX, 150).commit();
        wait(20);
    }

    function init() {
        steps = [];
    }

    function test_a_long_swipe_left_is_the_next_tab() {
        swipe(350, 150, 10, 20);
        compare(steps, [1]);
    }

    function test_a_long_swipe_right_is_the_previous_tab() {
        swipe(50, 250, 10, 20);
        compare(steps, [-1]);
    }

    function test_a_short_slow_drag_does_nothing() {
        swipe(200, 160, 8, 60);
        compare(steps, []);
    }

    function test_a_quick_flick_counts() {
        swipe(250, 190, 3, 5);
        compare(steps, [1]);
    }

    function test_a_vertical_list_scrolls_and_switches_nothing() {
        const touch = touchEvent(area);
        touch.press(0, list, 100, 180).commit();
        for (let i = 1; i <= 10; i++) {
            wait(20);
            touch.move(0, list, 100 - i * 3, 180 - i * 15).commit();
        }
        touch.release(0, list, 70, 30).commit();
        wait(50);
        verify(list.contentY > 0);
        compare(steps, []);
    }

    function test_a_horizontal_swipe_over_a_list_switches() {
        const touch = touchEvent(area);
        touch.press(0, list, 190, 100).commit();
        for (let i = 1; i <= 10; i++) {
            wait(20);
            touch.move(0, list, 190 - i * 18, 100).commit();
        }
        touch.release(0, list, 10, 100).commit();
        wait(20);
        compare(steps, [1]);
    }

    function test_a_slider_keeps_its_finger() {
        const touch = touchEvent(area);
        touch.press(0, slider, 10, 20).commit();
        for (let i = 1; i <= 10; i++) {
            wait(20);
            touch.move(0, slider, 10 + i * 15, 20).commit();
        }
        touch.release(0, slider, 160, 20).commit();
        wait(20);
        verify(slider.value > 0.5);
        compare(steps, []);
    }

    function test_a_mouse_drag_does_nothing() {
        mouseDrag(area, 350, 150, -250, 0);
        compare(steps, []);
    }
}

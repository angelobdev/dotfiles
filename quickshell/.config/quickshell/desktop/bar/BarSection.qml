pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import ".."
import "widgets/Registry.js" as Registry

// One of the five sections of the bar: its widgets in a row, each loaded from bar/widgets/. A widget with
// nothing to show (no player, no updates) is left out, except while the bar is edited, where it shows dimmed
// so it can still be moved.
Item {
    id: root
    required property string key
    // The bar window; each widget gets it as its bar.
    required property var panel
    property var ids: []
    readonly property bool editing: panel.editing
    // Room at the end for the + of the edit mode.
    readonly property int addRoom: editing ? Theme.hit(30) : 0
    readonly property int visibleCount: slots().length
    // Holds the window title, which takes the room it is given.
    readonly property bool fills: slots().some(slot => slot.fills)
    // The width the widgets need, with the title at its full length.
    readonly property real naturalWidth: visibleCount === 0 ? (editing ? Theme.hit(56) : 0) : row.implicitWidth + addRoom
    // The width they need when the title shrinks to nothing.
    readonly property real fixedWidth: {
        const shown = slots();
        if (shown.length === 0)
            return editing ? Theme.hit(56) : 0;
        let total = 0;
        for (const slot of shown)
            total += slot.fills ? 0 : slot.implicitWidth;
        return total + (shown.length - 1) * row.spacing + addRoom;
    }
    // The loaded widgets that show, in order.
    function slots() {
        const result = [];
        for (const child of row.children)
            if (child.isSlot && child.wanted)
                result.push(child);
        return result;
    }
    // Each shown widget as { index, x, width } in the coordinates of item.
    function geometry(item) {
        return slots().map(slot => {
            const point = slot.mapToItem(item, 0, 0);
            return {
                index: slot.index,
                x: point.x,
                width: slot.width
            };
        });
    }
    implicitWidth: naturalWidth
    implicitHeight: Theme.barHeight
    // Whether it shows; not visible, which also turns false while a parent is hidden.
    readonly property bool shows: editing || visibleCount > 0
    visible: shows
    RowLayout {
        id: row
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
        width: Math.max(0, root.width - root.addRoom)
        spacing: 5
        Repeater {
            model: root.ids
            Loader {
                id: slot
                required property string modelData
                required property int index
                readonly property bool isSlot: true
                readonly property bool fills: item?.fills ?? false
                readonly property bool shown: !!item && item.shown
                // Not visible itself: that turns false while the whole section is hidden, which would keep an
                // empty section hidden for good.
                readonly property bool wanted: !!item && (shown || root.editing)
                visible: wanted
                opacity: shown ? 1 : 0.45
                Layout.fillWidth: fills
                Layout.minimumWidth: fills ? 0 : -1
                Layout.fillHeight: item?.fillHeight ?? false
                Component.onCompleted: {
                    const widget = Registry.find(modelData);
                    if (widget)
                        setSource(Qt.resolvedUrl("widgets/" + widget.source), {
                            bar: root.panel
                        });
                }
            }
        }
    }
}

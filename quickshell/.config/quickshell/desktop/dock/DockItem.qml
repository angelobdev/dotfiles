import QtQuick
import Quickshell
import ".."
import "../components"
import "../services"
import "DockModel.js" as DockModel

Row {
    id: root
    required property var modelData
    required property int index
    // Supplied by the dock window: the pointer x relative to the dock centre (NaN when away), how far
    // the magnification has eased in (0–1), and the row layout the resting positions come from.
    property real pointerOffset: NaN
    property real zoomAmount: 0
    property int count: 1
    property int separatorIndex: -1
    // While a pin is dragged: how far this item slides aside, whether that slide animates, and whether
    // this item is the one being dragged (its slot stays empty; the window draws the moving icon).
    property real shift: 0
    property bool shiftAnimated: false
    property bool dragged: false
    // Keyboard selection (Super+D): the window draws the ring, the item shows its tooltip.
    property bool selected: false
    // Where the window anchors the selection ring and the context menu.
    readonly property Item anchorItem: cell
    readonly property int size: Theme.hit(Config.dockIconSize)
    readonly property int cellWidth: size + 8
    readonly property real zoom: 1 + (DockModel.magnify(pointerOffset - DockModel.baseOffset(index, count, separatorIndex, cellWidth, 13), cellWidth, Config.dockMagnification) - 1) * zoomAmount
    readonly property string label: modelData.entry?.name || modelData.appId
    signal menuRequested(var item, Item anchor)
    signal dragStarted(var item)
    signal dragMoved(point position)
    signal dragFinished(bool canceled)
    height: size + 20
    spacing: 0
    transform: Translate {
        x: root.shift
        Behavior on x {
            enabled: root.shiftAnimated
            NumberAnimation {
                duration: Theme.motionFast
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeOut
            }
        }
    }
    // Pinned apps and running-only apps are split by a hairline.
    Item {
        visible: root.modelData.separatorBefore
        width: 13
        height: parent.height
        Rectangle {
            anchors.centerIn: parent
            width: 1
            height: root.size * 0.7
            color: Theme.stroke
        }
    }
    Item {
        id: cell
        width: root.cellWidth * root.zoom
        height: parent.height
        Accessible.role: Accessible.Button
        Accessible.name: root.label
        // Magnified icons rise above the cell; the click area rises with them.
        MouseArea {
            id: mouse
            property point pressPoint: Qt.point(0, 0)
            property bool moved: false
            // A long press (touch) opens the menu like a right click; the release then does nothing.
            property bool held: false
            anchors {
                left: parent.left
                right: parent.right
                top: icon.top
                bottom: parent.bottom
            }
            hoverEnabled: true
            // Keep the pointer while a pin is dragged off the dock.
            preventStealing: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            pressAndHoldInterval: 500
            onPressed: event => {
                pressPoint = Qt.point(event.x, event.y);
                moved = false;
                held = false;
                Dock.touched();
            }
            onPressAndHold: event => {
                if (moved || event.button !== Qt.LeftButton)
                    return;
                held = true;
                root.menuRequested(root.modelData, cell);
            }
            // Pinned apps start dragging after 6 px (24 in tablet mode, where a finger always moves a little
            // while it taps); positions go to the window in its own coordinates.
            readonly property real dragThreshold: Tablet.active ? 24 : 6
            onPositionChanged: event => {
                if (!(pressedButtons & Qt.LeftButton) || !root.modelData.pinned)
                    return;
                if (!moved && Math.hypot(event.x - pressPoint.x, event.y - pressPoint.y) > dragThreshold) {
                    moved = true;
                    root.dragStarted(root.modelData);
                }
                if (moved)
                    root.dragMoved(mapToItem(null, event.x, event.y));
            }
            onReleased: if (moved)
                root.dragFinished(false)
            onCanceled: if (moved) {
                moved = false;
                root.dragFinished(true);
            }
            onClicked: event => {
                if (moved || held)
                    return;
                if (event.button === Qt.RightButton)
                    root.menuRequested(root.modelData, cell);
                else if (event.button === Qt.MiddleButton)
                    Dock.launchNew(root.modelData);
                else
                    Dock.activate(root.modelData);
            }
        }
        Image {
            id: icon
            anchors.horizontalCenter: parent.horizontalCenter
            // Grows upward from a fixed baseline above the running dot.
            y: 6 + root.size - height
            width: root.size * root.zoom
            height: root.size * root.zoom
            source: Quickshell.iconPath(root.modelData.entry?.icon || root.modelData.appId, "application-x-executable")
            // Rendered once at the largest size so magnifying never reloads the image.
            sourceSize: Qt.size(root.size * 2 * Math.max(1, Config.dockMagnification), root.size * 2 * Math.max(1, Config.dockMagnification))
            fillMode: Image.PreserveAspectFit
            opacity: root.dragged ? 0 : 1
            scale: mouse.pressed && !mouse.moved ? 0.92 : 1
            Behavior on scale {
                NumberAnimation {
                    duration: Theme.motionFast
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.easeOut
                }
            }
        }
        // Urgent windows pulse until they are focused or the hint clears.
        SequentialAnimation {
            running: root.modelData.urgent && Theme.motionSlow > 0
            loops: Animation.Infinite
            onRunningChanged: if (!running)
                icon.opacity = 1
            NumberAnimation {
                target: icon
                property: "opacity"
                to: 0.35
                duration: Theme.motionSlow * 2
                easing.type: Easing.InOutSine
            }
            NumberAnimation {
                target: icon
                property: "opacity"
                to: 1
                duration: Theme.motionSlow * 2
                easing.type: Easing.InOutSine
            }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 4
            visible: root.modelData.running
            width: root.modelData.active ? 14 : 4
            height: 4
            radius: 2
            color: root.modelData.urgent ? Theme.danger : root.modelData.active ? Theme.accent : Theme.muted
            Behavior on width {
                NumberAnimation {
                    duration: Theme.motionFast
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.easeOut
                }
            }
        }
        HintTooltip {
            target: cell
            text: root.label
            above: true
            gap: 8 + Math.max(0, -icon.y)
            hovered: mouse.containsMouse && !mouse.pressed || root.selected
        }
    }
}

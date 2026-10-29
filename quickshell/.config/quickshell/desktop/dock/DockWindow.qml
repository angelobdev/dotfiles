import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import ".."
import "../services"
import "DockModel.js" as DockModel

PanelWindow {
    id: root
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property var workspace: monitor?.activeWorkspace ?? null
    // Hyprspace fades Top layers like the bar; keep the surface mapped but out of the way.
    readonly property bool compositorHidden: BarVisibility.hidden(screen.name)
    readonly property bool fullscreen: workspace?.hasFullscreen ?? false
    // A focused special-workspace window (the AI assistant) covers an empty workspace.
    readonly property bool specialFocused: Hyprland.activeToplevel?.activated === true && Hyprland.activeToplevel.monitor === monitor && (Hyprland.activeToplevel.workspace?.name ?? "").startsWith("special:")
    readonly property bool emptyWorkspace: workspace !== null && workspace.toplevels.values.length === 0 && !specialFocused
    readonly property var request: Dock.requested[screen.name]
    property bool hovered: false
    // Set once the pointer is over the dock, so leaving it ends a shortcut request too.
    property bool visited: false
    // Pin being dragged, the pointer in window coordinates, and whether neighbours animate aside.
    property string dragKey: ""
    property point dragPoint: Qt.point(0, 0)
    property bool shiftAnimated: true
    readonly property int cellWidth: Config.dockIconSize + 8
    readonly property int separatorIndex: Dock.items.findIndex(i => i.separatorBefore)
    readonly property int dragFrom: dragKey === "" ? -1 : Dock.items.findIndex(i => i.key === dragKey)
    readonly property int dragTarget: dragFrom === -1 ? -1 : DockModel.dropIndex(dragPoint.x - width / 2, Dock.items.filter(i => i.pinned).length, Dock.items.length, separatorIndex, cellWidth, 13)
    // Lifting a pin more than an icon above the shelf removes it on release.
    readonly property bool dragRemoving: dragFrom !== -1 && dragPoint.y < body.y - Config.dockIconSize
    // Super+D hands the keyboard to this dock until Esc, Super+D, activation or an outside click.
    readonly property bool keyboardMode: Dock.keyboardScreen === screen.name && shown && Dock.menuScreen === ""
    property int selection: 0
    // Returning from the context menu keeps the selection the menu was opened from.
    property bool selectionKept: false
    readonly property bool shown: Config.dockEnabled && Dock.items.length > 0 && !compositorHidden && !fullscreen && (hovered || dragKey !== "" || Dock.menuScreen === screen.name || request === true || request !== false && (Dock.peeks[screen.name] !== undefined || emptyWorkspace))
    readonly property int margin: 8
    // Room above the shelf for magnified icons.
    readonly property real rise: Config.dockIconSize * Math.max(0, Config.dockMagnification - 1)
    // The surface keeps enough transparent room above the shelf to draw a pin being dragged off; input
    // stays limited to the mask, so the room never blocks windows underneath.
    readonly property real dragRoom: Config.dockIconSize * 2.5
    readonly property real pointerOffset: pointer.hovered ? pointer.point.position.x - width / 2 : NaN
    // Magnification eases in and out on entering and leaving; while moving it follows the pointer directly.
    property real zoomAmount: pointer.hovered && shown && dragKey === "" ? 1 : 0
    Behavior on zoomAmount {
        NumberAnimation {
            duration: Theme.motionFast
            easing.type: Easing.BezierSpline
            easing.bezierCurve: Theme.easeOut
        }
    }
    anchors {
        bottom: true
        left: true
        right: true
    }
    implicitHeight: body.height + margin * 2 + Math.max(rise, dragRoom)
    exclusiveZone: 0
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "desktop-dock"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: compositorHidden ? emptyInput : hitInput
    // Start on the focused app, or the first item.
    onKeyboardModeChanged: if (keyboardMode) {
        if (!selectionKept || selection >= Dock.items.length)
            selection = Math.max(0, Dock.items.findIndex(i => i.active));
        selectionKept = false;
    }
    onShownChanged: Dock.setShown(screen.name, shown)
    // A new request lasts until the pointer visits the dock after it, not because of an earlier visit.
    onRequestChanged: visited = pointer.hovered
    Component.onCompleted: Dock.setShown(screen.name, shown)
    Component.onDestruction: Dock.setShown(screen.name, false)
    function selectedItem() {
        return Dock.items[selection] ?? null;
    }
    function moveSelection(step) {
        const count = Dock.items.length;
        if (count > 0)
            selection = (selection + step + count) % count;
    }
    function openSelectedMenu() {
        const delegate = repeater.itemAt(selection);
        if (!delegate)
            return;
        selectionKept = true;
        menu.open(delegate.modelData, delegate.anchorItem);
    }
    function finishDrag(canceled) {
        // Snap rather than slide: after the reorder every neighbour already sits where its shift put it.
        shiftAnimated = false;
        if (!canceled && dragFrom !== -1) {
            if (dragRemoving)
                Dock.unpin(dragKey);
            else
                Dock.movePin(dragKey, dragTarget);
        }
        dragKey = "";
        Qt.callLater(() => shiftAnimated = true);
    }
    DockMenu {
        id: menu
        screen: root.screen
    }
    Region {
        id: emptyInput
        width: 0
        height: 0
    }
    // The strip stays in the input region while shown: otherwise a pointer resting on the edge beside the
    // dock falls outside it, the dock hides, the strip reveals it again, and it bounces.
    Region {
        id: hitInput
        item: bodyArea
        Region {
            item: strip
        }
    }
    Timer {
        id: reveal
        interval: Config.dockRevealDelay
        running: pointer.hovered && !root.hovered
        onTriggered: root.hovered = true
    }
    DockKeyboard {
        screen: root.screen
        active: root.keyboardMode
        hole: Qt.rect(bodyArea.x, root.screen.height - root.height + bodyArea.y, bodyArea.width, bodyArea.height)
        onStepRequested: direction => root.moveSelection(direction)
        onFirstRequested: root.selection = 0
        onLastRequested: root.selection = Math.max(0, Dock.items.length - 1)
        onActivateRequested: newInstance => {
            const item = root.selectedItem();
            if (!item)
                return;
            if (newInstance) {
                Dock.launchNew(item);
                Dock.endKeyboard(root.screen.name, false);
            } else {
                Dock.activate(item);
            }
        }
        onMenuRequested: root.openSelectedMenu()
        onCloseRequested: Dock.endKeyboard(root.screen.name, true)
        onOutsideClicked: Dock.endKeyboard(root.screen.name, false)
    }
    Timer {
        id: conceal
        interval: 400
        running: !pointer.hovered && root.visited && !root.keyboardMode
        onTriggered: {
            root.hovered = false;
            root.visited = false;
            Dock.release(root.screen.name);
        }
    }
    // Input only arrives inside the mask, so hovering the window means hovering the strip or the dock.
    // The handler sits on an ancestor of the icons: on a sibling below them, the hover-enabled
    // MouseArea of an icon took the hover away and the dock hid under the pointer.
    Item {
        anchors.fill: parent
        HoverHandler {
            id: pointer
            onHoveredChanged: if (hovered)
                root.visited = true
        }
        // A thin strip along the bottom edge, clear of the corners, plus the dock down to the edge while shown.
        Item {
            id: strip
            x: 64
            y: root.height - Config.dockTriggerHeight
            width: Math.max(0, root.width - 128)
            height: Config.dockTriggerHeight
        }
        Item {
            id: bodyArea
            x: body.x
            y: root.height - height
            width: root.shown ? body.width : 0
            height: root.shown ? body.height + root.margin + (pointer.hovered ? root.rise : 0) : 0
        }
        Rectangle {
            id: body
            anchors.horizontalCenter: parent.horizontalCenter
            y: root.shown ? root.height - height - root.margin : root.height + 2
            width: row.implicitWidth + 16
            height: Config.dockIconSize + 20
            radius: Theme.radius
            color: Theme.surface
            border.color: Theme.stroke
            opacity: root.shown ? 1 : 0
            Behavior on y {
                NumberAnimation {
                    duration: Theme.motionNormal
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: root.shown ? Theme.easeOut : Theme.easeIn
                }
            }
            Behavior on opacity {
                NumberAnimation {
                    duration: Theme.motionNormal
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: root.shown ? Theme.easeOut : Theme.easeIn
                }
            }
            Row {
                id: row
                anchors.centerIn: parent
                Repeater {
                    id: repeater
                    model: ScriptModel {
                        values: Dock.items
                        objectProp: "key"
                    }
                    DockItem {
                        pointerOffset: root.pointerOffset
                        zoomAmount: root.zoomAmount
                        count: Dock.items.length
                        separatorIndex: root.separatorIndex
                        shift: DockModel.dragShift(index, root.dragFrom, root.dragTarget, root.cellWidth)
                        shiftAnimated: root.shiftAnimated && root.dragKey !== ""
                        dragged: index === root.dragFrom
                        selected: root.keyboardMode && index === root.selection
                        onMenuRequested: (item, anchor) => menu.open(item, anchor)
                        onDragStarted: item => root.dragKey = item.key
                        onDragMoved: position => root.dragPoint = position
                        onDragFinished: canceled => root.finishDrag(canceled)
                    }
                }
            }
        }
        // Keyboard selection ring; it glides between items like the launcher highlight.
        Rectangle {
            readonly property var delegate: root.keyboardMode && Dock.items.length > 0 ? repeater.itemAt(root.selection) : null
            visible: delegate !== null
            x: delegate ? body.x + row.x + delegate.x + delegate.anchorItem.x : 0
            y: body.y + row.y + 2
            width: delegate ? delegate.anchorItem.width : 0
            height: Config.dockIconSize + 16
            radius: Theme.corner(12)
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
            Behavior on x {
                NumberAnimation {
                    duration: Theme.motionNormal
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.easeOut
                }
            }
        }
        // The pin being dragged follows the pointer; above the removal line it fades and says so.
        Image {
            id: floating
            readonly property var item: root.dragFrom === -1 ? null : Dock.items[root.dragFrom]
            visible: item !== null
            x: root.dragPoint.x - width / 2
            y: Math.max(0, root.dragPoint.y - height / 2)
            width: Config.dockIconSize
            height: Config.dockIconSize
            source: item ? Quickshell.iconPath(item.entry?.icon || item.appId, "application-x-executable") : ""
            sourceSize: Qt.size(width * 2, height * 2)
            fillMode: Image.PreserveAspectFit
            opacity: root.dragRemoving ? 0.55 : 1
        }
        Rectangle {
            visible: floating.visible && root.dragRemoving
            anchors {
                horizontalCenter: floating.horizontalCenter
                top: floating.bottom
                topMargin: 4
            }
            width: removeLabel.implicitWidth + 16
            height: removeLabel.implicitHeight + 6
            radius: height / 2
            color: Theme.tooltip
            border.color: Theme.stroke
            Text {
                id: removeLabel
                anchors.centerIn: parent
                text: I18n.tr("dock.remove")
                textFormat: Text.PlainText
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 12
            }
        }
    }
}

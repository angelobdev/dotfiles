import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import ".."
import "../services"

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
    readonly property bool shown: Config.dockEnabled && Dock.items.length > 0 && !compositorHidden && !fullscreen && (hovered || request === true || request !== false && (Dock.peeks[screen.name] !== undefined || emptyWorkspace))
    readonly property int margin: 8
    anchors {
        bottom: true
        left: true
        right: true
    }
    implicitHeight: body.height + margin * 2
    exclusiveZone: 0
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Top
    WlrLayershell.namespace: "desktop-dock"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: compositorHidden ? emptyInput : hitInput
    onShownChanged: Dock.setShown(screen.name, shown)
    Component.onCompleted: Dock.setShown(screen.name, shown)
    Component.onDestruction: Dock.setShown(screen.name, false)
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
    Timer {
        id: conceal
        interval: 400
        running: !pointer.hovered && root.visited
        onTriggered: {
            root.hovered = false;
            root.visited = false;
            Dock.release(root.screen.name);
        }
    }
    // Input only arrives inside the mask, so hovering the window means hovering the strip or the dock.
    // The handler sits on an ancestor of the icons: on a sibling below them, an icon's hover-enabled
    // MouseArea took the hover away and the dock hid under the pointer.
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
            y: root.height - body.height - root.margin
            width: root.shown ? body.width : 0
            height: root.shown ? body.height + root.margin : 0
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
                    model: ScriptModel {
                        values: Dock.items
                        objectProp: "key"
                    }
                    DockItem {}
                }
            }
        }
    }
}

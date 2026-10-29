import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."
import "../services"

PanelWindow {
    id: root
    required property string panelName
    // Panels with a multi-step Escape (cancel, then close) handle it themselves.
    property bool closeOnEscape: true
    // Centred dialogs scale from the middle; side panels slide down from the bar at the top right.
    property bool dialog: false
    readonly property bool open: ShellState.panel === panelName
    // 0 closed .. 1 open; the window stays mapped until the closing animation reaches 0.
    property real reveal: open ? 1 : 0
    property Scale motionScale: Scale {
        origin.x: root.dialog ? root.width / 2 : root.width - 12 - Config.controlCenterWidth / 2
        origin.y: root.dialog ? root.height / 2 : 58
        xScale: ShellState.navigation !== 0 ? 1 : 0.97 + 0.03 * root.reveal
        yScale: xScale
    }
    // Moving between the Control Center and a sub-panel pushes sideways: the new panel comes in from the
    // direction of travel while the old one leaves the other way.
    property Translate motionShift: Translate {
        x: ShellState.navigation === 0 ? 0 : (root.open ? 1 : -1) * ShellState.navigation * 24 * (1 - root.reveal)
        y: root.dialog || ShellState.navigation !== 0 ? 0 : -10 * (1 - root.reveal)
    }
    signal opened
    screen: ShellState.activeScreen || Quickshell.screens[0]
    visible: open || reveal > 0
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: Qt.rgba(Theme.scrim.r, Theme.scrim.g, Theme.scrim.b, Theme.scrim.a * reveal)
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-overlay"
    // A closing panel must not keep the keyboard or swallow clicks while it fades out. In tablet mode an open
    // panel takes the focus on demand: an exclusive layer receives every touch, so keys of the on-screen
    // keyboard never reached it, while the keyboard itself never takes the focus away from the panel.
    WlrLayershell.keyboardFocus: !open ? WlrKeyboardFocus.None : Tablet.active ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.Exclusive
    mask: !open ? passThrough : Keyboard.areaVisible && Keyboard.screenName === screen?.name ? aroundKeyboard : null
    Behavior on reveal {
        NumberAnimation {
            duration: root.open ? Theme.motionNormal : Theme.motionFast
            easing.type: Easing.BezierSpline
            easing.bezierCurve: root.open ? Theme.easeOut : Theme.easeIn
        }
    }
    onOpenChanged: if (open) {
        contentItem.forceActiveFocus();
        opened();
    }
    Component.onCompleted: {
        contentItem.transform = [motionScale, motionShift];
        // Reach full opacity early so the blur behind the card does not pop in late.
        contentItem.opacity = Qt.binding(() => Math.min(1, root.reveal * 2));
    }
    contentItem.Keys.onEscapePressed: if (closeOnEscape)
        ShellState.close()
    Region {
        id: passThrough
    }
    // The on-screen keyboard keeps its touches: an open panel takes none in its rectangle, whichever of the
    // two surfaces the compositor puts on top.
    Region {
        id: aroundKeyboard
        item: root.contentItem
        Region {
            intersection: Intersection.Subtract
            x: Keyboard.area.x
            y: Keyboard.area.y
            width: Keyboard.area.width
            height: Keyboard.area.height
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
}

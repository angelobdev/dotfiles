import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."

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
        xScale: 0.97 + 0.03 * root.reveal
        yScale: xScale
    }
    property Translate motionShift: Translate {
        y: root.dialog ? 0 : -10 * (1 - root.reveal)
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
    // A closing panel must not keep the keyboard or swallow clicks while it fades out.
    WlrLayershell.keyboardFocus: open ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
    mask: open ? null : passThrough
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
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
}

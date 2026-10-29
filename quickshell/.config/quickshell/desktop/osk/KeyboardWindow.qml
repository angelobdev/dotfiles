import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."
import "../services"

// The on-screen keyboard on the touch display, docked or floating. Neither surface takes keyboard focus,
// so keys reach the window that has it. Docked, the keyboard reserves its height and windows shrink above
// it; floating, it sits over them and moves by its strip.
Scope {
    id: root
    readonly property var target: Quickshell.screens.find(s => s.name === Config.primaryMonitor) ?? Quickshell.screens[0]
    PanelWindow {
        screen: root.target
        visible: Keyboard.shown && !Keyboard.floating
        anchors {
            left: true
            right: true
            bottom: true
        }
        implicitHeight: docked.implicitHeight
        color: Theme.background
        WlrLayershell.layer: WlrLayer.Top
        WlrLayershell.namespace: "desktop-osk"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        KeyboardView {
            id: docked
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
            }
            // Ten keys across a wide landscape screen would be too wide to type on.
            width: Math.min(parent.width, 1100)
        }
    }
    PanelWindow {
        id: floatingWindow
        screen: root.target
        visible: Keyboard.shown && Keyboard.floating
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        exclusionMode: ExclusionMode.Ignore
        color: "transparent"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-osk"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        mask: Region {
            item: floating
        }
        // Centred near the bottom each time it opens; a drag replaces these bindings until then.
        function place() {
            floating.x = Qt.binding(() => Math.round((floatingWindow.width - floating.width) / 2));
            floating.y = Qt.binding(() => Math.max(0, floatingWindow.height - floating.height - 24));
        }
        onVisibleChanged: if (visible)
            place()
        KeyboardView {
            id: floating
            floating: true
            dragTarget: floating
            x: Math.round((floatingWindow.width - width) / 2)
            y: Math.max(0, floatingWindow.height - height - 24)
            width: Math.min(floatingWindow.width - 32, 900)
        }
    }
}

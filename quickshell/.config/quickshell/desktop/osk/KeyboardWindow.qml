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
    // Both keyboards are Overlay layers, like the panels; a surface mapped later draws above the others of
    // its layer, so when a panel opens over a shown keyboard (the launcher focuses its search field) the
    // keyboard is mapped again on top of it.
    property bool raising: false
    Connections {
        target: Keyboard
        function onRaiseRequested() {
            root.raising = true;
            raise.restart();
        }
    }
    Binding {
        target: Keyboard
        property: "screenName"
        value: root.target?.name ?? ""
    }
    Binding {
        target: Keyboard
        property: "areaVisible"
        value: dockedWindow.visible || floatingWindow.visible
    }
    Binding {
        target: Keyboard
        property: "reserved"
        value: dockedWindow.visible ? dockedWindow.height : 0
    }
    Binding {
        target: Keyboard
        property: "area"
        value: floatingWindow.visible ? Qt.rect(floatingView.x, floatingView.y, floatingView.width, floatingView.height) : Qt.rect(0, dockedWindow.screen ? dockedWindow.screen.height - dockedWindow.height : 0, dockedWindow.width, dockedWindow.height)
    }
    // Long enough for the unmap to reach the compositor, so the map that follows is a new one.
    Timer {
        id: raise
        interval: 60
        onTriggered: root.raising = false
    }
    // Floating windows do not move for a reserved area by themselves; once Hyprland has applied the new
    // one, rules.lua fits them into what is left (the assistant console is tiled and follows by itself).
    Timer {
        id: refit
        interval: 200
        onTriggered: Quickshell.execDetached(["hyprctl", "eval", "if desktop_fit_floating then desktop_fit_floating() end"])
    }
    PanelWindow {
        id: dockedWindow
        screen: root.target
        // Over the lock screen the keyboard is always docked (rules.lua lets this namespace above the lock).
        visible: Keyboard.shown && (!Keyboard.floating || Keyboard.locked) && !root.raising
        // The keys are built the first time it shows and kept: never on a laptop, once in tablet mode.
        property bool used: false
        onVisibleChanged: {
            if (visible)
                used = true;
            if (!root.raising)
                refit.restart();
        }
        anchors {
            left: true
            right: true
            bottom: true
        }
        implicitHeight: docked.item?.implicitHeight ?? 0
        color: Theme.background
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-osk"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
        Loader {
            id: docked
            active: dockedWindow.used
            anchors {
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
            }
            // Ten keys across a wide landscape screen would be too wide to type on.
            width: Math.min(parent.width, 1100)
            sourceComponent: KeyboardView {}
        }
    }
    PanelWindow {
        id: floatingWindow
        screen: root.target
        visible: Keyboard.shown && Keyboard.floating && !Keyboard.locked && !root.raising
        // Built the first time it shows and kept, like the docked one.
        property bool used: false
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
            item: floatingView
        }
        // Centred near the bottom each time it opens; a drag replaces these bindings until then.
        function place() {
            floatingView.x = Qt.binding(() => Math.round((floatingWindow.width - floatingView.width) / 2));
            floatingView.y = Qt.binding(() => Math.max(0, floatingWindow.height - floatingView.height - 24));
        }
        onVisibleChanged: if (visible) {
            used = true;
            place();
        }
        // The loader is what moves (the keyboard drags it by its strip) and what the input region follows.
        Loader {
            id: floatingView
            active: floatingWindow.used
            x: Math.round((floatingWindow.width - width) / 2)
            y: Math.max(0, floatingWindow.height - height - 24)
            width: Math.min(floatingWindow.width - 32, 900)
            sourceComponent: KeyboardView {
                floating: true
                dragTarget: floatingView
            }
        }
    }
}

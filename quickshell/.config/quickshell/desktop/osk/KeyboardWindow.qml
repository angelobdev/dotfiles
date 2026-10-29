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
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel !== "")
                Keyboard.raise();
        }
    }
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
        value: floatingWindow.visible ? Qt.rect(floating.x, floating.y, floating.width, floating.height) : Qt.rect(0, dockedWindow.screen ? dockedWindow.screen.height - dockedWindow.height : 0, dockedWindow.width, dockedWindow.height)
    }
    // Long enough for the unmap to reach the compositor, so the map that follows is a new one.
    Timer {
        id: raise
        interval: 60
        onTriggered: root.raising = false
    }
    // Floating windows (the assistant of Super+A) do not move for a reserved area by themselves; once
    // Hyprland has applied the new one, rules.lua fits them into what is left.
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
        onVisibleChanged: if (!root.raising)
            refit.restart()
        anchors {
            left: true
            right: true
            bottom: true
        }
        implicitHeight: docked.implicitHeight
        color: Theme.background
        WlrLayershell.layer: WlrLayer.Overlay
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
        visible: Keyboard.shown && Keyboard.floating && !Keyboard.locked && !root.raising
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

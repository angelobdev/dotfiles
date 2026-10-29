import QtQuick
import Quickshell
import Quickshell.Wayland
import "../services"

// The drop-down assistant console closes on a click or tap outside it. While it is open on this screen,
// this transparent layer under every window takes those presses: the special workspace keeps them from
// the windows below it (input.special_fallthrough is off), so nothing else gets them.
PanelWindow {
    id: root
    // From the screen model (reading screen.name here loops: mapping the window updates it).
    required property string screenName
    visible: screenName !== "" && Agent.consoleScreen === screenName
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Bottom
    WlrLayershell.namespace: "desktop-console-catcher"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onPressed: Agent.hideConsole(root.screenName)
    }
}

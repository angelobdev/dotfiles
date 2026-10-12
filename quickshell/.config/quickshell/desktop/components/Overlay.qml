import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."
PanelWindow {
    id: root
    required property string panelName
    signal opened()
    screen: ShellState.activeScreen || Quickshell.screens[0]
    visible: ShellState.panel === panelName
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    color: "#18060c16"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-overlay"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    onVisibleChanged: if (visible) { contentItem.forceActiveFocus(); opened(); }
    contentItem.Keys.onEscapePressed: ShellState.close()
    MouseArea { anchors.fill: parent; onClicked: ShellState.close() }
}

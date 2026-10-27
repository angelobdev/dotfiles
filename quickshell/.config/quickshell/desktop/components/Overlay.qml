import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."

PanelWindow {
    id: root
    required property string panelName
    // Panels with a multi-step Escape (cancel, then close) handle it themselves.
    property bool closeOnEscape: true
    signal opened
    screen: ShellState.activeScreen || Quickshell.screens[0]
    visible: ShellState.panel === panelName
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: Theme.scrim
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-overlay"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    onVisibleChanged: if (visible) {
        contentItem.forceActiveFocus();
        opened();
    }
    contentItem.Keys.onEscapePressed: if (closeOnEscape)
        ShellState.close()
    MouseArea {
        anchors.fill: parent
        onClicked: ShellState.close()
    }
}

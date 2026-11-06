import QtQuick
import Quickshell
import Quickshell.Wayland
import "../services"

// The empty desktop of one screen: a transparent layer under every window, over the wallpaper, that opens
// the desktop menu on a right click or a long press (touch). Windows are above it, so their clicks never
// reach it. While the assistant console is open on this screen, ConsoleCatcher takes the presses instead.
PanelWindow {
    id: root
    // From the screen model (reading screen.name here loops: mapping the window updates it).
    required property string screenName
    signal menuRequested(real x, real y)
    visible: screenName !== "" && Agent.consoleScreen !== screenName
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Bottom
    WlrLayershell.namespace: "desktop-menu-catcher"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        pressAndHoldInterval: 500
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                root.menuRequested(mouse.x, mouse.y);
        }
        onPressAndHold: mouse => {
            if (mouse.button === Qt.LeftButton)
                root.menuRequested(mouse.x, mouse.y);
        }
    }
}

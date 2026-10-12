import QtQuick
import Quickshell
import Quickshell.Wayland
import ".."
PanelWindow {
    anchors { top: true; bottom: true; left: true; right: true }
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.layer: WlrLayer.Background
    WlrLayershell.namespace: "desktop-background"
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: "#101723" }
            GradientStop { position: 1; color: "#202039" }
        }
        Text {
            anchors { right: parent.right; bottom: parent.bottom; margins: 32 }
            text: "hyprland / quickshell"
            color: "#525570"
            font.family: Theme.font
            font.pixelSize: 14
        }
    }
}

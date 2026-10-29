import QtQuick
import Quickshell
import ".."
import "../components"
import "../services"

Row {
    id: root
    required property var modelData
    readonly property int size: Config.dockIconSize
    readonly property string label: modelData.entry?.name || modelData.appId
    height: size + 20
    spacing: 0
    // Pinned apps and running-only apps are split by a hairline.
    Item {
        visible: root.modelData.separatorBefore
        width: 13
        height: parent.height
        Rectangle {
            anchors.centerIn: parent
            width: 1
            height: root.size * 0.7
            color: Theme.stroke
        }
    }
    Item {
        id: cell
        width: root.size + 8
        height: parent.height
        Accessible.role: Accessible.Button
        Accessible.name: root.label
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton
            onClicked: event => {
                if (event.button === Qt.MiddleButton)
                    Dock.launchNew(root.modelData);
                else
                    Dock.activate(root.modelData);
            }
        }
        Image {
            id: icon
            anchors.horizontalCenter: parent.horizontalCenter
            y: 6
            width: root.size
            height: root.size
            source: Quickshell.iconPath(root.modelData.entry?.icon || root.modelData.appId, "application-x-executable")
            sourceSize: Qt.size(root.size * 2, root.size * 2)
            fillMode: Image.PreserveAspectFit
            scale: mouse.pressed ? 0.92 : mouse.containsMouse ? 1.08 : 1
            Behavior on scale {
                NumberAnimation {
                    duration: Theme.motionFast
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.easeOut
                }
            }
        }
        // Urgent windows pulse until they are focused or the hint clears.
        SequentialAnimation {
            running: root.modelData.urgent && Theme.motionSlow > 0
            loops: Animation.Infinite
            onRunningChanged: if (!running)
                icon.opacity = 1
            NumberAnimation {
                target: icon
                property: "opacity"
                to: 0.35
                duration: Theme.motionSlow * 2
                easing.type: Easing.InOutSine
            }
            NumberAnimation {
                target: icon
                property: "opacity"
                to: 1
                duration: Theme.motionSlow * 2
                easing.type: Easing.InOutSine
            }
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 4
            visible: root.modelData.running
            width: root.modelData.active ? 14 : 4
            height: 4
            radius: 2
            color: root.modelData.urgent ? Theme.danger : root.modelData.active ? Theme.accent : Theme.muted
            Behavior on width {
                NumberAnimation {
                    duration: Theme.motionFast
                    easing.type: Easing.BezierSpline
                    easing.bezierCurve: Theme.easeOut
                }
            }
        }
        HintTooltip {
            target: cell
            text: root.label
            above: true
            hovered: mouse.containsMouse && !mouse.pressed
        }
    }
}

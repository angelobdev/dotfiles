import QtQuick
import Quickshell.Services.UPower
import "../.."
import "../../services"
import ".."

// The assistant: a dot while its agent works (accent), asks (danger) or finished unseen; the panel on click.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Agent.available && Installed.has("assistant")
    iconName: "assistant"
    tooltip: Agent.title
    Accessible.name: Agent.title
    onClicked: ShellState.toggle("agent", root.bar.screen)
    Rectangle {
        id: agentDot
        readonly property bool asking: Agent.state === "permission" || Agent.state === "error"
        readonly property bool pulsing: Agent.state === "working" && !Theme.reduceMotion
        // On battery the dot blinks in two steps instead of fading: a fade redraws the bar on every frame
        // (120 a second here) for as long as the assistant works, and Hyprland composites each one.
        readonly property bool animated: pulsing && !UPower.onBattery
        property real pulse: 1
        visible: Agent.state === "working" || asking || Agent.unseen
        opacity: pulsing ? pulse : 1
        anchors {
            right: parent.right
            top: parent.top
            rightMargin: 3
            topMargin: 4
        }
        width: 7
        height: 7
        radius: 3.5
        color: asking ? Theme.danger : BarStyle.accent
        Timer {
            interval: 700
            repeat: true
            running: agentDot.pulsing && !agentDot.animated
            onTriggered: agentDot.pulse = agentDot.pulse < 1 ? 1 : 0.35
            onRunningChanged: agentDot.pulse = 1
        }
        SequentialAnimation on pulse {
            running: agentDot.animated
            loops: Animation.Infinite
            NumberAnimation {
                to: 0.35
                duration: 700
                easing.type: Easing.InOutSine
            }
            NumberAnimation {
                to: 1
                duration: 700
                easing.type: Easing.InOutSine
            }
        }
    }
}

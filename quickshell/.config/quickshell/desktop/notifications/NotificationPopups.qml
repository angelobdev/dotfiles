import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Services.Notifications
import ".."
import "../services"

PanelWindow {
    id: root
    screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) || Quickshell.screens[0]
    anchors {
        top: true
        right: true
    }
    margins {
        top: 54
        right: 12
    }
    readonly property int count: Notices.popups.length
    implicitWidth: 380
    // Full available height so a leaving toast is never clipped; the input mask still covers only the stack.
    implicitHeight: (screen?.height ?? 900) - 100
    visible: (count > 0 || leaving.running) && !Notices.quiet && ShellState.panel === ""
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-notifications"
    contentItem.clip: true
    mask: Region {
        item: stack
    }
    onCountChanged: if (count === 0)
        leaving.restart()
    // Keeps the window mapped while the last toast slides out.
    Timer {
        id: leaving
        interval: Theme.motionNormal
    }
    ListView {
        id: stack
        width: parent.width
        height: Math.min(contentHeight, parent.height)
        interactive: false
        spacing: 10
        // Reusing delegates keeps the other toasts (and their timers) alive when one leaves.
        model: ScriptModel {
            values: Notices.popups
            objectProp: "id"
        }
        add: Transition {
            NumberAnimation {
                property: "x"
                from: 48
                to: 0
                duration: Theme.motionNormal
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeOut
            }
            NumberAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: Theme.motionNormal
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeOut
            }
        }
        remove: Transition {
            NumberAnimation {
                property: "x"
                to: 64
                duration: Theme.motionFast
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeIn
            }
            NumberAnimation {
                property: "opacity"
                to: 0
                duration: Theme.motionFast
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeIn
            }
        }
        displaced: Transition {
            NumberAnimation {
                properties: "x,y"
                duration: Theme.motionNormal
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeOut
            }
        }
        delegate: Notice {
            id: toast
            required property var modelData
            width: stack.width
            notification: modelData
            popup: true
            onHidePopup: Notices.hidePopup(modelData.id)
            Timer {
                interval: toast.modelData.expireTimeout > 0 ? toast.modelData.expireTimeout : 6000
                running: toast.modelData.expireTimeout !== 0 && toast.modelData.urgency !== NotificationUrgency.Critical
                onTriggered: Notices.hidePopup(toast.modelData.id)
            }
            // Retain in the center after the toast timeout; dismiss/close stays explicit.
        }
    }
}

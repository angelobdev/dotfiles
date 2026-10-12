import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Services.Notifications
import ".."
import "../components"
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
    implicitWidth: 380
    implicitHeight: Math.min(stack.implicitHeight, (screen?.height ?? 900) - 100)
    visible: Notices.popups.length > 0 && !Notices.quiet && ShellState.panel === ""
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-notifications"
    contentItem.clip: true
    mask: Region {
        item: stack
    }
    Column {
        id: stack
        width: parent.width
        spacing: 10
        Repeater {
            model: Notices.popups
            Notice {
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
}

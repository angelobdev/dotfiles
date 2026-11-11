import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"
import "NotificationDeck.js" as NotificationDeck

Overlay {
    id: root
    // Decks are grouped as in the popups; those opened with the button under their newest entry.
    property var openStacks: ShellState.recall("notifications/openStacks", [])
    onOpenStacksChanged: ShellState.remember("notifications/openStacks", openStacks)
    readonly property var stacks: NotificationDeck.collapse(Notices.entries, openStacks)
    // The ages on the cards count to this; it moves only while the center is open.
    property real now: Date.now()
    panelName: "notifications"
    Timer {
        interval: 30000
        repeat: true
        running: root.open
        triggeredOnStart: true
        onTriggered: root.now = Date.now()
    }
    SidePanelCard {
        height: Math.min(600, parent.height - Theme.panelClearance)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("notifications.title")
                PanelIconButton {
                    iconName: Notices.quiet ? "bell-off" : "bell"
                    tooltip: I18n.tr("notifications.doNotDisturb")
                    highlighted: Notices.quiet
                    tone: "state"
                    onClicked: Notices.setQuiet(!Notices.quiet)
                }
                PanelIconButton {
                    iconName: "trash"
                    tooltip: I18n.tr("notifications.clearAll")
                    enabled: Notices.entries.length > 0
                    onClicked: Notices.clear()
                }
            }
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 10
                // Live notifications and the archive kept across shell restarts.
                model: ScriptModel {
                    values: root.stacks.entries
                    objectProp: "id"
                }
                add: Transition {
                    NumberAnimation {
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                    NumberAnimation {
                        property: "scale"
                        from: 0.96
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
                    required property var modelData
                    readonly property string stackKey: root.stacks.keys[modelData?.id] ?? ""
                    width: list.width
                    notification: modelData
                    now: root.now
                    stackCount: root.stacks.counts[modelData?.id] ?? 1
                    stackOpen: stackCount > 1 && root.openStacks.includes(stackKey)
                    onStackToggled: root.openStacks = stackOpen ? root.openStacks.filter(key => key !== stackKey) : root.openStacks.concat(stackKey)
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    text: I18n.tr("notifications.empty")
                    visible: list.count === 0
                    color: Theme.muted
                }
            }
        }
    }
}

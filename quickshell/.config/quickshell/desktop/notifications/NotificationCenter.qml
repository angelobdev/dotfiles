import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

Overlay {
    panelName: "notifications"
    SidePanelCard {
        height: Math.min(600, parent.height - 76)
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
                    values: Notices.entries
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
                    width: list.width
                    notification: modelData
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

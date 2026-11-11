pragma ComponentBehavior: Bound
import QtQuick
import "../components"
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../services"
import "WorkspaceModel.js" as WorkspaceModel

RowLayout {
    id: root
    required property var workspaces
    required property int activeId
    // The id of a workspace opened by scrolling past the last pill; -1 opens none.
    property int newId: -1
    property bool scrollEnabled: true
    property real accumulated: 0
    property bool pixelGesture: false
    signal activated(int id)
    spacing: 0
    function scroll(angle, pixels) {
        if (!scrollEnabled || workspaces.length === 0)
            return;
        const usePixels = pixels !== 0;
        const delta = usePixels ? pixels : angle;
        if (!delta)
            return;
        if (pixelGesture !== usePixels || accumulated * delta < 0)
            accumulated = 0;
        pixelGesture = usePixels;
        accumulated += delta;
        reset.restart();
        const threshold = usePixels ? 30 : 120;
        const steps = Math.trunc(accumulated / threshold);
        if (!steps)
            return;
        accumulated -= steps * threshold;
        const next = WorkspaceModel.scrollTarget(workspaces, activeId, -steps, newId);
        if (next >= 0)
            activated(next);
    }
    Timer {
        id: reset
        interval: 200
        onTriggered: root.accumulated = 0
    }
    WheelHandler {
        target: null
        enabled: root.scrollEnabled
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: event => {
            root.scroll(event.angleDelta.y, event.pixelDelta.y);
            event.accepted = true;
        }
    }
    Repeater {
        // Reuse pills by workspace id so updates do not rebuild them (and width animations run).
        model: ScriptModel {
            values: root.workspaces
            objectProp: "id"
        }
        Button {
            id: workspace
            required property var modelData
            readonly property bool active: root.activeId === modelData.id
            // A click would leave keyboard focus behind, and with it the focus background.
            focusPolicy: Qt.NoFocus
            implicitWidth: active ? Theme.hit(46) : Theme.hit(28)
            implicitHeight: Theme.hit(28)
            Accessible.name: I18n.tr("workspaces.accessibleName", [modelData.id])
            HintTooltip {
                target: workspace
                hovered: workspace.hovered
                text: I18n.plural("workspaces.windowCount.one", "workspaces.windowCount.other", workspace.modelData.count, [workspace.modelData.id])
            }
            background: Rectangle {
                radius: Theme.corner(10)
                color: workspace.hovered || workspace.activeFocus ? Theme.raised : "transparent"
            }
            contentItem: Item {
                Rectangle {
                    anchors.centerIn: parent
                    width: workspace.active ? 28 : 8
                    height: 8
                    radius: 4
                    visible: !Config.workspaceNumbers
                    color: workspace.active ? BarStyle.accent : workspace.modelData.urgent ? Theme.danger : BarStyle.muted
                    Behavior on width {
                        NumberAnimation {
                            duration: Theme.motionFast
                        }
                    }
                }
                // With numbers on, the active pill becomes a taller badge and the others the bare number.
                Rectangle {
                    anchors.centerIn: parent
                    width: workspace.active ? 28 : 0
                    height: Theme.textSize(11) + 6
                    radius: height / 2
                    visible: Config.workspaceNumbers
                    color: BarStyle.accent
                    Behavior on width {
                        NumberAnimation {
                            duration: Theme.motionFast
                        }
                    }
                }
                Text {
                    anchors.centerIn: parent
                    visible: Config.workspaceNumbers
                    text: workspace.modelData.id
                    font.pixelSize: Theme.textSize(11)
                    font.bold: workspace.active
                    // The active number sits on the accent pill, so it takes the other bar text colour.
                    color: workspace.active ? BarStyle.halo : workspace.modelData.urgent ? Theme.danger : BarStyle.muted
                }
            }
            onClicked: root.activated(modelData.id)
        }
    }
}

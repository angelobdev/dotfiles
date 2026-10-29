import QtQuick
import "../components"
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../services"

RowLayout {
    id: root
    required property var workspaces
    required property int activeId
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
        const current = workspaces.findIndex(w => w.id === activeId);
        if (current < 0)
            return;
        const next = Math.max(0, Math.min(workspaces.length - 1, current - steps));
        if (next !== current)
            activated(workspaces[next].id);
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
            implicitWidth: active ? Theme.hit(46) : Theme.hit(28)
            implicitHeight: Theme.hit(28)
            Accessible.name: I18n.tr("workspaces.accessibleName", [modelData.id])
            HintTooltip {
                target: workspace
                hovered: workspace.hovered
                text: I18n.tr(workspace.modelData.count === 1 ? "workspaces.windowCount.one" : "workspaces.windowCount.other", [workspace.modelData.id, workspace.modelData.count])
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
                    color: workspace.active ? BarStyle.accent : workspace.modelData.urgent ? Theme.danger : BarStyle.muted
                    Behavior on width {
                        NumberAnimation {
                            duration: 160
                        }
                    }
                }
            }
            onClicked: root.activated(modelData.id)
        }
    }
}

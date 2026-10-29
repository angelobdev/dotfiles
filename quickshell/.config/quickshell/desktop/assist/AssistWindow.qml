import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import ".."
import "../components"
import "../services"
import "AssistModel.js" as AssistModel

// The floating assist button on the touch display. The surface covers the screen but takes input only on
// the button, or everywhere while the menu is open (a tap outside closes it); it never takes keyboard
// focus, so the app underneath keeps it (the on-screen keyboard relies on that).
PanelWindow {
    id: root
    readonly property int size: 56
    readonly property int margin: 16
    readonly property int top: Theme.barHeight
    readonly property string placeKey: (screen?.name ?? "") + ":" + (width >= height ? "landscape" : "portrait")
    property var position: Assist.positionFor(placeKey)
    property bool idle: false
    readonly property bool dragging: drag.active
    screen: Quickshell.screens.find(s => s.name === Config.primaryMonitor) ?? Quickshell.screens[0]
    visible: Assist.shown
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-assist"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    mask: Region {
        item: button
        Region {
            item: outside
        }
    }
    function wake() {
        idle = false;
        idleTimer.restart();
    }
    function settle() {
        const placed = AssistModel.place(position, size, width, height, top, margin, idle && !Assist.menuOpen ? 0.45 : 0);
        button.x = placed.x;
        button.y = placed.y;
        Qt.callLater(placeMenu);
    }
    // Placed after the grid has its size, beside where the button comes to rest (it may still be moving).
    function placeMenu() {
        const resting = AssistModel.place(position, size, width, height, top, margin, 0);
        const origin = AssistModel.menuOrigin(resting, size, position.side, menu.width, menu.height, width, height, top, margin, 12);
        menu.x = origin.x;
        menu.y = origin.y;
    }
    onPlaceKeyChanged: {
        position = Assist.positionFor(placeKey);
        settle();
    }
    onWidthChanged: settle()
    onHeightChanged: settle()
    onIdleChanged: settle()
    onVisibleChanged: {
        if (visible) {
            wake();
            settle();
        }
    }
    Connections {
        target: Assist
        function onMenuOpenChanged() {
            root.wake();
            root.settle();
        }
    }
    Timer {
        id: idleTimer
        interval: 3000
        onTriggered: root.idle = !Assist.menuOpen && !root.dragging
    }
    // While the menu is open the whole screen takes input; a tap outside the menu closes it. Closed, this
    // item has no size, so the input region is the button alone (anchors.fill would override the size).
    Item {
        id: outside
        visible: Assist.menuOpen
        width: Assist.menuOpen ? parent.width : 0
        height: Assist.menuOpen ? parent.height : 0
        TapHandler {
            onTapped: Assist.menuOpen = false
        }
    }
    Card {
        id: menu
        visible: Assist.menuOpen
        width: grid.implicitWidth + 24
        height: grid.implicitHeight + 24
        onWidthChanged: Qt.callLater(root.placeMenu)
        onHeightChanged: Qt.callLater(root.placeMenu)
        color: Theme.background
        opacity: Assist.menuOpen ? 1 : 0
        scale: Assist.menuOpen ? 1 : 0.92
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.motionFast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.motionFast
            }
        }
        GridLayout {
            id: grid
            anchors.centerIn: parent
            columns: 4
            rowSpacing: 8
            columnSpacing: 8
            Repeater {
                model: Assist.actions
                Rectangle {
                    id: action
                    required property var modelData
                    implicitWidth: 100
                    implicitHeight: 84
                    radius: Theme.corner(16)
                    color: tap.pressed ? Theme.raised : modelData.active ? Qt.alpha(Theme.accent, 0.22) : Theme.tile
                    ColumnLayout {
                        anchors.centerIn: parent
                        width: parent.width - 8
                        spacing: 6
                        Icon {
                            Layout.alignment: Qt.AlignHCenter
                            name: action.modelData.icon
                            color: action.modelData.active ? Theme.accent : Theme.text
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                        }
                        Text {
                            Layout.fillWidth: true
                            text: action.modelData.label
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: 11
                        }
                    }
                    TapHandler {
                        id: tap
                        onTapped: Assist.run(action.modelData.name)
                    }
                }
            }
        }
    }
    Item {
        id: button
        width: root.size
        height: root.size
        Behavior on x {
            enabled: !root.dragging
            NumberAnimation {
                duration: Theme.motionNormal
                easing.type: Easing.OutCubic
            }
        }
        Behavior on y {
            enabled: !root.dragging
            NumberAnimation {
                duration: Theme.motionNormal
                easing.type: Easing.OutCubic
            }
        }
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: Theme.background
            border.width: Theme.frameWidth
            border.color: Assist.menuOpen ? Theme.frameActive : Theme.frameInactive
            opacity: root.idle && !Assist.menuOpen ? 0.5 : 1
            Behavior on opacity {
                NumberAnimation {
                    duration: Theme.motionNormal
                }
            }
            Rectangle {
                anchors.centerIn: parent
                width: 34
                height: 34
                radius: width / 2
                color: "transparent"
                border.width: 2
                border.color: Theme.muted
                Rectangle {
                    anchors.centerIn: parent
                    width: 18
                    height: 18
                    radius: width / 2
                    color: Assist.menuOpen ? Theme.accent : Theme.text
                }
            }
        }
        DragHandler {
            id: drag
            target: button
            xAxis.minimum: 0
            xAxis.maximum: root.width - root.size
            yAxis.minimum: root.top
            yAxis.maximum: root.height - root.size
            onActiveChanged: {
                if (active) {
                    Assist.menuOpen = false;
                    root.wake();
                    return;
                }
                root.position = AssistModel.snap(button.x, button.y, root.size, root.width, root.height, root.top, root.margin);
                Assist.savePosition(root.placeKey, root.position);
                root.wake();
                root.settle();
            }
        }
        TapHandler {
            longPressThreshold: 0.5
            onTapped: Assist.menuOpen = !Assist.menuOpen
            onLongPressed: Assist.run(Config.assistLongPress)
        }
        HoverHandler {
            onHoveredChanged: if (hovered)
                root.wake()
        }
        Accessible.role: Accessible.Button
        Accessible.name: I18n.tr("assist.title")
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Networking
import Quickshell.Services.SystemTray
import Quickshell.Services.UPower
import ".."
import "../components"
import "../services"
import "../components/WorkspaceModel.js" as WorkspaceModel

PanelWindow {
    id: bar
    anchors {
        top: true
        left: true
        right: true
    }
    margins {
        top: 0
        left: 0
        right: 0
    }
    implicitHeight: 38
    color: "transparent"
    WlrLayershell.namespace: "desktop-bar"
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property var workspaces: WorkspaceModel.build(
        Hyprland.workspaces.values.map(w => ({id: w.id, monitor: w.monitor?.name, count: w.toplevels.values.length, urgent: w.urgent})),
        Hyprland.monitors.values.map(m => ({name: m.name, activeId: m.activeWorkspace?.id})), Config.minimumWorkspaces)[screen.name] || []
    function focusWorkspace(id) {
        Hyprland.dispatch("hl.dsp.focus({ monitor = " + JSON.stringify(screen.name) + " })");
        Hyprland.dispatch("hl.dsp.focus({ workspace = " + id + " })");
    }
    readonly property int battery: Math.round((UPower.displayDevice?.percentage ?? 0) * 100)
    // Keep the inhibitor on a mapped surface, independent of the control panel.
    IdleInhibitor {
        window: bar
        enabled: Idle.keepAwake
    }
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }
    Rectangle {
        anchors.fill: parent
        radius: 0
        // border.color: Theme.stroke
        gradient: Gradient {
            GradientStop {
                position: 0
                color: '#55000000'
            }
            GradientStop {
                position: 1
                color: '#44000000'
            }
        }
    }
    RowLayout {
        anchors {
            fill: parent
            leftMargin: 8
            rightMargin: 8
        }
        spacing: 5
        BarButton {
            iconSource: Quickshell.iconPath("fedora-logo-icon", "start-here")
            iconSize: 18
            implicitWidth: 32
            tooltip: "Applicazioni"
            onClicked: ShellState.toggle("launcher", bar.screen)
        }
        RowLayout {
            id: workspaceRow
            spacing: 0
            WheelHandler {
                target: null
                property real accumulated: 0
                onWheel: event => {
                    if (!Config.workspaceScroll) { event.accepted = false; return; }
                    accumulated += event.angleDelta.y;
                    if (Math.abs(accumulated) < 120) return;
                    const index = bar.workspaces.findIndex(w => w.id === bar.monitor?.activeWorkspace?.id);
                    const target = Math.max(0, Math.min(bar.workspaces.length - 1, index + (accumulated < 0 ? 1 : -1)));
                    accumulated = 0;
                    if (bar.workspaces[target]) bar.focusWorkspace(bar.workspaces[target].id);
                }
            }
            Repeater {
                model: bar.workspaces
                Button {
                    id: workspace
                    required property var modelData
                    readonly property bool active: bar.monitor?.activeWorkspace?.id === modelData.id
                    implicitWidth: active ? 46 : 28
                    implicitHeight: 28
                    Accessible.name: "Workspace " + modelData.id
                    HintTooltip {
                        target: workspace
                        hovered: workspace.hovered
                        text: "Workspace " + workspace.modelData.id + " · " + workspace.modelData.count + " finestre"
                    }
                    background: Rectangle {
                        radius: 10
                        color: workspace.hovered || workspace.activeFocus ? Theme.raised : "transparent"
                    }
                    contentItem: Item {
                        Rectangle {
                            anchors.centerIn: parent
                            width: workspace.active ? 28 : 8
                            height: 8
                            radius: 4
                            color: workspace.active ? Theme.accent : workspace.modelData.urgent ? Theme.danger : Theme.muted
                            Behavior on width {
                                NumberAnimation {
                                    duration: 160
                                }
                            }
                        }
                    }
                    onClicked: bar.focusWorkspace(modelData.id)
                }
            }
        }
        Text {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.leftMargin: 12
            text: Hyprland.activeToplevel?.title ?? "Desktop"
            elide: Text.ElideRight
            textFormat: Text.PlainText
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
            visible: bar.width > 1100
        }
        Item {
            Layout.fillWidth: true
            visible: bar.width <= 1100
        }
        Repeater {
            model: SystemTray.items
            Item {
                id: trayItem
                required property var modelData
                implicitWidth: 28
                implicitHeight: 28
                Image {
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    source: trayItem.modelData.icon
                }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
                    onClicked: mouse => {
                        if (mouse.button === Qt.MiddleButton)
                            trayItem.modelData.secondaryActivate();
                        else if (mouse.button === Qt.RightButton || trayItem.modelData.onlyMenu) {
                            if (trayItem.modelData.hasMenu) {
                                const point = mapToItem(bar.contentItem, mouse.x, mouse.y);
                                trayItem.modelData.display(bar, point.x, point.y);
                            }
                        } else
                            trayItem.modelData.activate();
                    }
                    onWheel: event => trayItem.modelData.scroll(event.angleDelta.y, false)
                }
            }
        }
        BarButton {
            visible: Recording.running
            iconName: "record"
            destructive: true
            text: Recording.elapsed
            tooltip: "Registrazione in corso · Clic per fermare e salvare"
            onClicked: Recording.stop()
        }
        BarButton {
            id: batteryButton
            readonly property string profileIcon: PowerProfiles.profile === PowerProfile.PowerSaver ? "leaf" : PowerProfiles.profile === PowerProfile.Performance ? "performance" : ""
            readonly property string profileLabel: PowerProfiles.profile === PowerProfile.PowerSaver ? "Risparmio energetico" : PowerProfiles.profile === PowerProfile.Performance ? "Prestazioni" : PowerProfiles.profile === PowerProfile.Balanced ? "Bilanciato" : "Profilo non disponibile"
            visible: UPower.displayDevice?.isLaptopBattery ?? false
            iconName: !UPower.onBattery ? "battery-charging" : bar.battery < 20 ? "battery-low" : "battery"
            text: bar.battery + "%"
            implicitWidth: batteryContent.implicitWidth + leftPadding + rightPadding
            tooltip: (UPower.onBattery ? "Alimentazione a batteria" : "Alimentazione collegata") + " · " + profileLabel
            Accessible.name: "Batteria " + text + " · " + profileLabel
            contentItem: RowLayout {
                id: batteryContent
                spacing: 6
                Icon {
                    visible: batteryButton.profileIcon !== ""
                    name: batteryButton.profileIcon
                    color: batteryButton.foreground
                    Layout.preferredWidth: batteryButton.iconSize
                    Layout.preferredHeight: batteryButton.iconSize
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: batteryButton.text
                    font: batteryButton.font
                    color: batteryButton.foreground
                    verticalAlignment: Text.AlignVCenter
                    textFormat: Text.PlainText
                }
                Icon {
                    name: batteryButton.iconName
                    color: batteryButton.foreground
                    Layout.preferredWidth: batteryButton.iconSize
                    Layout.preferredHeight: batteryButton.iconSize
                    Layout.alignment: Qt.AlignVCenter
                }
            }
            onClicked: ShellState.toggle("battery", bar.screen)
        }
        BarButton {
            iconName: "keyboard"
            tooltip: "Hints · Scorciatoie"
            onClicked: ShellState.toggle("hints", bar.screen)
        }
        BarButton {
            iconName: Notices.quiet ? "bell-off" : "bell"
            tooltip: Notices.quiet ? "Notifiche · Non disturbare" : "Notifiche"
            onClicked: ShellState.toggle("notifications", bar.screen)
        }
        BarButton {
            iconName: "controls"
            tooltip: "Centro di controllo"
            highlighted: ShellState.panel === "controls"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        BarButton {
            text: Qt.formatDateTime(clock.date, "ddd d MMM  HH:mm")
            tooltip: "Calendario"
            onClicked: ShellState.toggle("calendar", bar.screen)
            Layout.leftMargin: 3
            Layout.rightMargin: 3
        }
        BarButton {
            iconName: "power"
            tooltip: "Sessione"
            onClicked: ShellState.toggle("power", bar.screen)
        }
    }
}

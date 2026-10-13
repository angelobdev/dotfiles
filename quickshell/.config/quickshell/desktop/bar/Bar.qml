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
import "tray"
import "WorkspaceModel.js" as WorkspaceModel

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
    // Keep the surface mapped: Hyprspace restores its alpha when it closes.
    // An invisible bar must neither reserve space nor intercept preview clicks.
    readonly property bool compositorHidden: BarVisibility.hidden(screen.name)
    exclusiveZone: compositorHidden ? 0 : implicitHeight
    mask: compositorHidden ? emptyInput : null
    Region {
        id: emptyInput
        width: 0
        height: 0
    }
    readonly property var monitor: Hyprland.monitorFor(screen)
    readonly property var workspaces: WorkspaceModel.build(Hyprland.workspaces.values.map(w => ({
                id: w.id,
                monitor: w.monitor?.name,
                count: w.toplevels.values.length,
                urgent: w.urgent
            })), Hyprland.monitors.values.map(m => ({
                name: m.name,
                activeId: m.activeWorkspace?.id
            })), Config.minimumWorkspaces)[screen.name] || []
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
    TrayMenuWindow {
        id: trayMenu
        screen: bar.screen
    }
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel !== "")
                trayMenu.dismiss();
        }
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
        WorkspaceStrip {
            Layout.fillHeight: true
            workspaces: bar.workspaces
            activeId: bar.monitor?.activeWorkspace?.id ?? -1
            scrollEnabled: Config.workspaceScroll
            onActivated: id => bar.focusWorkspace(id)
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
                                trayMenu.menuEntry = trayItem.modelData.menu;
                                trayMenu.popup(trayItem, 0, trayItem.height + 8);
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

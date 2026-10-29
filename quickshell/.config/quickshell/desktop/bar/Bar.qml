import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
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
    // Double-click on an empty part of the bar switches between the shaded and the transparent bar.
    Item {
        anchors.fill: parent
        TapHandler {
            onDoubleTapped: BarStyle.toggle()
        }
    }
    Rectangle {
        anchors.fill: parent
        opacity: BarStyle.transparent ? 0 : 1
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.motionNormal
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Theme.easeOut
            }
        }
        gradient: Gradient {
            GradientStop {
                position: 0
                color: Theme.barShadeTop
            }
            GradientStop {
                position: 1
                color: Theme.barShadeBottom
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
            tooltip: I18n.tr("launcher.title")
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
            text: Hyprland.activeToplevel?.title ?? I18n.tr("bar.desktop")
            elide: Text.ElideRight
            textFormat: Text.PlainText
            color: BarStyle.muted
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
            tooltip: I18n.tr("recording.barTooltip")
            onClicked: Recording.stop()
        }
        BarButton {
            id: batteryButton
            readonly property string profileIcon: PowerProfiles.profile === PowerProfile.PowerSaver ? "leaf" : PowerProfiles.profile === PowerProfile.Performance ? "performance" : ""
            readonly property string profileLabel: PowerProfiles.profile === PowerProfile.PowerSaver ? I18n.tr("battery.profiles.powerSaver") : PowerProfiles.profile === PowerProfile.Performance ? I18n.tr("battery.profiles.performance") : PowerProfiles.profile === PowerProfile.Balanced ? I18n.tr("battery.profiles.balanced") : I18n.tr("battery.profileUnavailable")
            visible: UPower.displayDevice?.isLaptopBattery ?? false
            iconName: !UPower.onBattery ? "battery-charging" : "battery-" + Math.round(bar.battery / 25) * 25
            text: bar.battery + "%"
            implicitWidth: batteryContent.implicitWidth + leftPadding + rightPadding
            tooltip: (UPower.onBattery ? I18n.tr("battery.onBattery") : I18n.tr("battery.pluggedIn")) + " · " + profileLabel
            Accessible.name: I18n.tr("battery.accessiblePrefix") + text + " · " + profileLabel
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
            tooltip: I18n.tr("hints.tooltip")
            onClicked: ShellState.toggle("hints", bar.screen)
        }
        BarButton {
            iconName: Notices.quiet ? "bell-off" : "bell"
            tooltip: Notices.quiet ? I18n.tr("notifications.quietTooltip") : I18n.tr("notifications.title")
            onClicked: ShellState.toggle("notifications", bar.screen)
        }
        BarButton {
            iconName: "controls"
            tooltip: I18n.tr("controlCenter.title")
            highlighted: ShellState.panel === "controls"
            onClicked: ShellState.toggle("controls", bar.screen)
        }
        BarButton {
            text: I18n.locale.toString(clock.date, I18n.tr("bar.clockFormat"))
            tooltip: I18n.tr("calendar.title")
            onClicked: ShellState.toggle("calendar", bar.screen)
            Layout.leftMargin: 3
            Layout.rightMargin: 3
        }
        BarButton {
            iconName: "power"
            tooltip: I18n.tr("session.title")
            onClicked: ShellState.toggle("power", bar.screen)
        }
    }
}

import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// The Control Center switches in a 2x2 grid: Do Not Disturb, Keep awake, Rotation lock (only with an
// accelerometer) and Night shift, whose mode and temperature open below the grid.
ColumnLayout {
    id: root
    property bool details: false
    spacing: 10
    function nightStatus() {
        if (!NightShift.available)
            return I18n.tr("nightShift.missing");
        if (NightShift.mode === "on")
            return I18n.tr("nightShift.kelvin", [NightShift.temperature]);
        if (NightShift.mode === "auto")
            return NightShift.active ? I18n.tr("nightShift.until", [Config.nightShiftEnd]) : I18n.tr("nightShift.from", [Config.nightShiftStart]);
        return I18n.tr("common.off");
    }
    GridLayout {
        Layout.fillWidth: true
        columns: 2
        rowSpacing: 10
        columnSpacing: 10
        ToggleTile {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            icon: Notices.quiet ? "bell-off" : "bell"
            title: I18n.tr("notifications.doNotDisturb")
            status: Notices.quiet ? I18n.tr("notifications.silenced") : I18n.tr("notifications.enabled")
            checked: Notices.quiet
            onToggled: Notices.setQuiet(!Notices.quiet)
        }
        ToggleTile {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            icon: "coffee"
            title: I18n.tr("idle.keepAwake")
            status: Idle.keepAwake ? I18n.tr("idle.inhibited") : I18n.tr("idle.automatic")
            checked: Idle.keepAwake
            onToggled: Idle.setKeepAwake(!Idle.keepAwake)
        }
        ToggleTile {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            visible: Tablet.available
            icon: Tablet.locked ? "rotate-lock" : "rotate"
            title: I18n.tr("tablet.rotationLock")
            status: Tablet.locked ? I18n.tr("tablet.locked") : Tablet.active ? I18n.tr("tablet.rotatesAutomatically") : I18n.tr("tablet.rotatesInTablet")
            checked: Tablet.locked
            onToggled: Tablet.setLocked(!Tablet.locked)
        }
        ToggleTile {
            Layout.fillWidth: true
            Layout.preferredWidth: 1
            icon: "night"
            title: I18n.tr("nightShift.title")
            status: root.nightStatus()
            checked: NightShift.active
            available: NightShift.available
            hasDetails: true
            detailsOpen: root.details
            onToggled: NightShift.toggle()
            onDetailsRequested: root.details = !root.details
        }
    }
    Expander {
        expanded: root.details && NightShift.available
        spacing: 8
        ChoiceChips {
            options: [
                {
                    name: "off",
                    label: I18n.tr("nightShift.modes.off")
                },
                {
                    name: "on",
                    label: I18n.tr("nightShift.modes.on")
                },
                {
                    name: "auto",
                    label: I18n.tr("nightShift.modes.auto")
                }
            ]
            current: NightShift.mode
            onChosen: name => NightShift.setMode(name)
        }
        Text {
            Layout.fillWidth: true
            text: I18n.tr("nightShift.schedule", [Config.nightShiftStart, Config.nightShiftEnd])
            wrapMode: Text.WordWrap
            font.family: Theme.font
            font.pixelSize: 11
            color: Theme.muted
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Text {
                text: I18n.tr("nightShift.kelvin", [slider.value])
                font.family: Theme.font
                font.pixelSize: 12
                color: Theme.text
                Layout.preferredWidth: 60
            }
            ControlSlider {
                id: slider
                Layout.fillWidth: true
                from: NightShift.minimum
                to: NightShift.maximum
                stepSize: 100
                value: NightShift.temperature
                // Saved and sent to hyprsunset once the drag ends; arrow keys apply each step.
                onPressedChanged: if (!pressed)
                    NightShift.setTemperature(value)
                onMoved: if (!pressed)
                    NightShift.setTemperature(value)
                Accessible.name: I18n.tr("nightShift.temperature")
            }
        }
    }
}

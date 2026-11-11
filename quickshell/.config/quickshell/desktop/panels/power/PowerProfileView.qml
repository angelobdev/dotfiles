import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower
import "../.."
import "../../components"
import "../../services"

// The power profile (Power Saver, Balanced, Performance) and, on a laptop, Power Saver at low battery. The
// battery panel and Settings → Power both show it.
ColumnLayout {
    id: root
    // A laptop battery is there: the automatic Power Saver applies only then.
    property bool laptop: (UPower.displayDevice?.ready ?? false) && (UPower.displayDevice?.isLaptopBattery ?? false)
    spacing: 8
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ActionButton {
            Layout.fillWidth: true
            iconName: "leaf"
            tooltip: I18n.tr("battery.profiles.powerSaver")
            highlighted: PowerProfiles.profile === PowerProfile.PowerSaver
            tone: "state"
            onClicked: PowerProfiles.profile = PowerProfile.PowerSaver
        }
        ActionButton {
            Layout.fillWidth: true
            iconName: "balanced"
            tooltip: I18n.tr("battery.profiles.balanced")
            highlighted: PowerProfiles.profile === PowerProfile.Balanced
            tone: "state"
            onClicked: PowerProfiles.profile = PowerProfile.Balanced
        }
        ActionButton {
            Layout.fillWidth: true
            iconName: "performance"
            tooltip: I18n.tr("battery.profiles.performance")
            enabled: PowerProfiles.hasPerformanceProfile
            highlighted: PowerProfiles.profile === PowerProfile.Performance
            tone: "state"
            onClicked: PowerProfiles.profile = PowerProfile.Performance
        }
    }
    RowLayout {
        visible: root.laptop
        Layout.fillWidth: true
        Text {
            Layout.fillWidth: true
            text: I18n.tr("battery.autoSaver", [Config.batteryLow])
            wrapMode: Text.Wrap
            color: Theme.text
            font.pixelSize: Theme.textSize(13)
        }
        ControlSwitch {
            checked: Battery.autoSaver
            onToggled: Battery.setAutoSaver(checked)
            Accessible.name: I18n.tr("battery.autoSaver", [Config.batteryLow])
        }
    }
}

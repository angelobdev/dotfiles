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
    readonly property string profileName: PowerProfiles.profile === PowerProfile.PowerSaver ? I18n.tr("battery.profiles.powerSaver") : PowerProfiles.profile === PowerProfile.Performance ? I18n.tr("battery.profiles.performance") : I18n.tr("battery.profiles.balanced")
    spacing: 8
    // The segment of a profile; hover is a light neutral wash, so it never reads darker than the chosen one.
    component Segment: ActionButton {
        id: seg
        tone: "state"
        background: Rectangle {
            radius: Theme.corner(11)
            color: seg.highlighted ? Theme.active : seg.down || seg.hovered || seg.activeFocus ? Theme.selection : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: Theme.motionFast
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        Segment {
            Layout.fillWidth: true
            iconName: "leaf"
            tooltip: I18n.tr("battery.profiles.powerSaver")
            highlighted: PowerProfiles.profile === PowerProfile.PowerSaver
            onClicked: PowerProfiles.profile = PowerProfile.PowerSaver
        }
        Segment {
            Layout.fillWidth: true
            iconName: "balanced"
            tooltip: I18n.tr("battery.profiles.balanced")
            highlighted: PowerProfiles.profile === PowerProfile.Balanced
            onClicked: PowerProfiles.profile = PowerProfile.Balanced
        }
        Segment {
            Layout.fillWidth: true
            iconName: "performance"
            tooltip: I18n.tr("battery.profiles.performance")
            enabled: PowerProfiles.hasPerformanceProfile
            highlighted: PowerProfiles.profile === PowerProfile.Performance
            onClicked: PowerProfiles.profile = PowerProfile.Performance
        }
    }
    // The chosen profile by name: "Risparmio energetico" does not fit beside an icon in a third of the panel.
    Text {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        text: root.profileName
        color: Theme.text
        font.pixelSize: Theme.textSize(13)
        elide: Text.ElideRight
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

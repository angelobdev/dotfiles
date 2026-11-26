import QtQuick
import QtQuick.Layouts
import Quickshell.Services.UPower
import "../.."
import "../../components"
import "../../services"
import ".."

BarButton {
    id: root
    property var bar
    readonly property bool shown: UPower.displayDevice?.isLaptopBattery ?? false
    readonly property int battery: Math.round((UPower.displayDevice?.percentage ?? 0) * 100)
    readonly property string profileIcon: PowerProfiles.profile === PowerProfile.PowerSaver ? "leaf" : PowerProfiles.profile === PowerProfile.Performance ? "performance" : ""
    readonly property string profileLabel: PowerProfiles.profile === PowerProfile.PowerSaver ? I18n.tr("battery.profiles.powerSaver") : PowerProfiles.profile === PowerProfile.Performance ? I18n.tr("battery.profiles.performance") : PowerProfiles.profile === PowerProfile.Balanced ? I18n.tr("battery.profiles.balanced") : I18n.tr("battery.profileUnavailable")
    iconName: !UPower.onBattery ? "battery-charging" : "battery-" + Math.round(battery / 25) * 25
    text: battery + "%"
    implicitWidth: batteryContent.implicitWidth + leftPadding + rightPadding
    tooltip: I18n.tr("battery.tooltip", [UPower.onBattery ? I18n.tr("battery.onBattery") : I18n.tr("battery.pluggedIn"), profileLabel])
    Accessible.name: I18n.tr("battery.accessible", [text, profileLabel])
    contentItem: RowLayout {
        id: batteryContent
        // The gap between icon and label of every other bar button.
        spacing: 10
        Icon {
            visible: root.profileIcon !== ""
            name: root.profileIcon
            color: root.foreground
            Layout.preferredWidth: root.iconSize
            Layout.preferredHeight: root.iconSize
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: root.text
            font: root.font
            color: root.foreground
            verticalAlignment: Text.AlignVCenter
            textFormat: Text.PlainText
        }
        Icon {
            name: root.iconName
            color: root.foreground
            Layout.preferredWidth: root.iconSize
            Layout.preferredHeight: root.iconSize
            Layout.alignment: Qt.AlignVCenter
        }
    }
    onClicked: ShellState.toggle("battery", root.bar.screen)
}

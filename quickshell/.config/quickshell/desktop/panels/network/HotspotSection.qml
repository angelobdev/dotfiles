import QtQuick
import QtQuick.Layouts
import ".."
import "../.."
import "../../components"
import "../../services"

// The Wi-Fi hotspot: on and off, its name and its password, on the list page of the Network panel.
ColumnLayout {
    id: section
    // The Network panel (panels/NetworkPanel.qml).
    required property var panel
    // Hides the password again, when the panel closes.
    function reset() {
        hotspotPassword.reset();
    }
    visible: section.panel.wifiDevices.length > 0
    Layout.fillWidth: true
    spacing: 6
    Heading {
        text: I18n.tr("network.hotspot")
        section: true
    }
    // One card, as the other groups of the Network panel: its switch and the password keep in from the edges.
    GroupCard {
        Layout.fillWidth: true
        verticalPadding: 6
        leftPadding: 6
        rightPadding: 6
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Layout.rightMargin: 6
            spacing: 10
            Icon {
                name: "hotspot"
                Layout.leftMargin: 12
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: I18n.tr("network.hotspotName")
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
                Text {
                    Layout.fillWidth: true
                    text: NetworkInfo.hotspot.active ? I18n.tr("network.hotspotOn", [NetworkInfo.hotspot.ssid]) : I18n.tr("network.hotspotOff")
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                    elide: Text.ElideRight
                    textFormat: Text.PlainText
                }
                Text {
                    Layout.fillWidth: true
                    text: I18n.tr("network.hotspotHint")
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                }
            }
            ControlSwitch {
                enabled: !NetworkInfo.busy
                onToggled: NetworkInfo.run(checked ? "hotspot-on" : "hotspot-off", checked ? [section.panel.wifiDevices[0].name] : [])
                Accessible.name: I18n.tr("network.hotspot")
                Binding on checked {
                    value: NetworkInfo.hotspot.active === true
                    when: !NetworkInfo.busy
                }
            }
        }
        NetworkPassword {
            id: hotspotPassword
            visible: NetworkInfo.hotspot.active === true
            Layout.fillWidth: true
            // Its label under the hotspot icon; its icon buttons at the edge, as the other icon buttons of the panel.
            Layout.leftMargin: 12
            uuid: NetworkInfo.hotspot.uuid ?? ""
            name: NetworkInfo.hotspot.ssid ?? ""
        }
    }
}

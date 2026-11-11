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
    spacing: 8
    Heading {
        text: I18n.tr("network.hotspot")
        section: true
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Icon {
            name: "hotspot"
            Layout.leftMargin: 12
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        Text {
            Layout.fillWidth: true
            text: NetworkInfo.hotspot.active ? I18n.tr("network.hotspotOn", [NetworkInfo.hotspot.ssid]) : I18n.tr("network.hotspotHint")
            color: NetworkInfo.hotspot.active ? Theme.text : Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(NetworkInfo.hotspot.active ? 13 : 11)
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
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
        uuid: NetworkInfo.hotspot.uuid ?? ""
        name: NetworkInfo.hotspot.ssid ?? ""
    }
}

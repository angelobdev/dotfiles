import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// VPN connections and Tailscale, on the list page of the Network panel.
ColumnLayout {
    id: section
    // The Network panel (panels/NetworkPanel.qml).
    required property var panel
    visible: NetworkInfo.vpns.length > 0 || NetworkInfo.tailscale.installed === true
    Layout.fillWidth: true
    Heading {
        text: I18n.tr("network.vpn")
        section: true
    }
    RowLayout {
        visible: NetworkInfo.tailscale.installed === true
        Layout.fillWidth: true
        spacing: 10
        Icon {
            name: "vpn"
            Layout.leftMargin: 12
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: I18n.tr("network.tailscale")
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
            }
            Text {
                Layout.fillWidth: true
                text: section.panel.tailscaleSummary
                color: Theme.muted
                font.pixelSize: Theme.textSize(11)
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
        }
        ControlSwitch {
            enabled: !NetworkInfo.busy && ["Running", "Stopped"].includes(NetworkInfo.tailscale.state)
            onToggled: NetworkInfo.run(checked ? "tailscale-up" : "tailscale-down", [])
            Accessible.name: I18n.tr("network.tailscale")
            Binding on checked {
                value: NetworkInfo.tailscale.state === "Running"
                when: !NetworkInfo.busy
            }
        }
    }
    Repeater {
        model: NetworkInfo.vpns
        ActionButton {
            required property var modelData
            Layout.fillWidth: true
            alignLeft: true
            iconName: "vpn"
            text: modelData.name
            highlighted: modelData.active
            tone: "state"
            enabled: !NetworkInfo.busy
            onClicked: NetworkInfo.run(modelData.active ? "vpn-down" : "vpn-up", [modelData.uuid])
        }
    }
}

import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "bluetooth"

Overlay {
    id: root
    panelName: "bluetooth"
    SidePanelCard {
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                settingsSection: "bluetooth"
                Layout.fillWidth: true
                title: I18n.tr("bluetooth.title")
                showBack: true
            }
            BluetoothView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                shown: root.visible
            }
        }
    }
}

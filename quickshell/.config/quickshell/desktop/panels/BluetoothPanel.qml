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
                Layout.fillWidth: true
                title: I18n.tr("bluetooth.title")
                showBack: true
            }
            BluetoothView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                shown: root.visible
            }
            // The full section of Settings, in place of this panel.
            ActionButton {
                Layout.alignment: Qt.AlignRight
                compact: true
                text: I18n.tr("settings.open")
                onClicked: ShellState.openSection("settings", "bluetooth", ShellState.activeScreen, false)
            }
        }
    }
}

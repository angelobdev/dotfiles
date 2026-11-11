import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "audio"

// Sound: a side panel under the bar like its siblings Network and Bluetooth, pushed from the Control Center.
Overlay {
    panelName: "audio"
    SidePanelCard {
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("audio.panelTitle")
                showBack: true
                settingsSection: "sound"
            }
            AudioView {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
        }
    }
}

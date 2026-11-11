import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "audio"

Overlay {
    panelName: "audio"
    dialog: true
    Card {
        anchors.centerIn: parent
        width: Math.min(620, parent.width - 48)
        height: Math.min(640, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
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

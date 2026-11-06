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
            Heading {
                text: I18n.tr("audio.panelTitle")
            }
            AudioView {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            RowLayout {
                ActionButton {
                    iconName: "arrow-left"
                    text: I18n.tr("controlCenter.title")
                    onClicked: ShellState.back()
                }
                Item {
                    Layout.fillWidth: true
                }
                // The full section of Settings, in place of this panel.
                ActionButton {
                    text: I18n.tr("settings.open")
                    onClicked: ShellState.openSection("settings", "sound", ShellState.activeScreen, false)
                }
                ActionButton {
                    text: I18n.tr("common.close")
                    onClicked: ShellState.close()
                }
            }
        }
    }
}

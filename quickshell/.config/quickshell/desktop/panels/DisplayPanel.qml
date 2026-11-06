import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "displays"

// Displays (Super + P, the F1 key of the OmniBook): the monitors and their mode (displays/DisplayView.qml).
Overlay {
    id: root
    panelName: "displays"
    dialog: true
    Card {
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 48)
        height: column.implicitHeight + 2 * Theme.dialogPadding
        ColumnLayout {
            id: column
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.dialogPadding
            }
            spacing: 14
            PanelHeader {
                title: I18n.tr("displays.title")
                Layout.fillWidth: true
            }
            DisplayView {
                Layout.fillWidth: true
                shown: root.visible
            }
            // The full section of Settings, in place of this panel.
            ActionButton {
                Layout.alignment: Qt.AlignRight
                compact: true
                text: I18n.tr("settings.open")
                onClicked: ShellState.openSection("settings", "displays", ShellState.activeScreen, false)
            }
        }
    }
}

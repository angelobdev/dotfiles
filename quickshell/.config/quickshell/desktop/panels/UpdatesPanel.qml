import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "updates"

// Available updates, opened from the bar icon that shows while there are any (or desktop-shell toggle
// updates): what would be updated, when it was checked, and Update, which opens a terminal on the updates
// screen of the guided installer (desktop-updates upgrade, desktop-manager updates).
Overlay {
    id: root
    panelName: "updates"
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 2 * Theme.panelPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: layout
            anchors.fill: parent
            anchors.margins: Theme.panelPadding
            spacing: 12
            PanelHeader {
                title: I18n.tr("updates.title")
                Layout.fillWidth: true
            }
            UpdatesView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                shown: root.visible
            }
            // The full section of Settings, in place of this panel.
            ActionButton {
                Layout.alignment: Qt.AlignRight
                compact: true
                text: I18n.tr("settings.open")
                onClicked: ShellState.openSection("settings", "updates", ShellState.activeScreen, false)
            }
        }
    }
}

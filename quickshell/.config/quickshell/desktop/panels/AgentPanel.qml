import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "agent"

// The AI coding assistant panel, opened from its bar icon: what the active agent is doing, rate-limit meters
// when the agent reports them, model and context use, and the drop-down console.
Overlay {
    id: root
    panelName: "agent"
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 2 * Theme.panelPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: layout
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                margins: Theme.panelPadding
            }
            spacing: 14
            PanelHeader {
                title: Agent.name
                Layout.fillWidth: true
            }
            AgentView {
                Layout.fillWidth: true
                shown: root.visible
            }
            // The full section of Settings, in place of this panel.
            ActionButton {
                Layout.alignment: Qt.AlignRight
                compact: true
                text: I18n.tr("settings.open")
                onClicked: ShellState.openSection("settings", "assistant", ShellState.activeScreen, false)
            }
        }
    }
}

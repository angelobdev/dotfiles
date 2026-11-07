import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "agent"

// The Claude Code assistant, opened from its bar icon: what Claude is doing, the subscription usage its
// status line reports (agent.py), and the drop-down console.
Overlay {
    id: root
    panelName: "agent"
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 2 * Theme.panelPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: layout
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.panelPadding
            }
            spacing: 14
            PanelHeader {
                title: Agent.herdr ? I18n.tr("assistant.agents") : I18n.tr("assistant.claude")
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

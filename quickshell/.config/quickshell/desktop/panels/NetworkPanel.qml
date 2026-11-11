import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "network"

Overlay {
    id: root
    panelName: "network"
    closeOnEscape: false
    contentItem.Keys.onEscapePressed: {
        if (!view.goBack())
            ShellState.close();
    }
    SidePanelCard {
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                settingsSection: "network"
                Layout.fillWidth: true
                title: view.title
                showBack: true
                backToControls: !view.inDetails
                backTooltip: view.inDetails ? I18n.tr("network.title") : I18n.tr("controlCenter.title")
                onBack: view.closeDetails()
            }
            NetworkView {
                id: view
                Layout.fillWidth: true
                Layout.fillHeight: true
                shown: root.visible
            }
        }
    }
}

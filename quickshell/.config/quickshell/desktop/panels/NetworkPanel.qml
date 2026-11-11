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
    // Overlay focuses its content item when it opens, after the view asked for the search field: the field would
    // stay unfocused (no accent outline) in the side panel, unlike in Settings. In tablet mode it waits for a tap.
    onOpened: if (!Tablet.active)
        Qt.callLater(() => view.focusItem.forceActiveFocus())
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

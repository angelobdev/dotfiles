import QtQuick
import QtQuick.Layouts
import ".."

RowLayout {
    id: root
    property string title: ""
    property bool showBack: false
    // Panels with an inner view handle Back themselves instead of returning to the Control Center.
    property bool backToControls: true
    property string backTooltip: I18n.tr("controlCenter.title")
    // The section of Settings that holds all of what this panel shows; a button opens it in place of the panel.
    // showSettings without a section opens Settings where it was left.
    property string settingsSection: ""
    property bool showSettings: settingsSection !== ""
    default property alias actions: actionsRow.data
    readonly property alias closeButton: closeIcon
    signal back
    spacing: 6
    PanelIconButton {
        visible: root.showBack
        iconName: "arrow-left"
        tooltip: root.backTooltip
        onClicked: {
            if (root.backToControls)
                ShellState.back();
            else
                root.back();
        }
    }
    Heading {
        text: root.title
        font.pixelSize: Theme.textSize(16)
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        elide: Text.ElideRight
    }
    RowLayout {
        id: actionsRow
        spacing: 2
    }
    PanelIconButton {
        visible: root.showSettings
        iconName: "controls"
        tooltip: I18n.tr("settings.open")
        onClicked: ShellState.openSection("settings", root.settingsSection || ShellState.recall("settings/section", "appearance"), ShellState.activeScreen, false)
    }
    PanelIconButton {
        id: closeIcon
        iconName: "close"
        tooltip: I18n.tr("common.close")
        onClicked: ShellState.close()
    }
}

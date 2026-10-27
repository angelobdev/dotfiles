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
                ShellState.toggle("controls", ShellState.activeScreen);
            else
                root.back();
        }
    }
    Heading {
        text: root.title
        font.pixelSize: 16
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        elide: Text.ElideRight
    }
    RowLayout {
        id: actionsRow
        spacing: 2
    }
    PanelIconButton {
        id: closeIcon
        iconName: "close"
        tooltip: I18n.tr("common.close")
        onClicked: ShellState.close()
    }
}

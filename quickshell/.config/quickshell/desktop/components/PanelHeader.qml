import QtQuick
import QtQuick.Layouts
import ".."

RowLayout {
    id: root
    property string title: ""
    property bool showBack: false
    default property alias actions: actionsRow.data
    spacing: 6
    PanelIconButton {
        visible: root.showBack
        iconName: "arrow-left"
        tooltip: I18n.tr("controlCenter.title")
        onClicked: ShellState.toggle("controls", ShellState.activeScreen)
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
        iconName: "close"
        tooltip: I18n.tr("common.close")
        onClicked: ShellState.close()
    }
}

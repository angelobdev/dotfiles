import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"

MenuItem {
    id: root
    property var entry: null
    text: entry?.text ?? subMenu?.title ?? ""
    enabled: entry?.enabled ?? subMenu?.enabled ?? true
    checkable: entry ? entry.buttonType !== QsMenuButtonType.None : false
    checked: entry?.checkState === Qt.Checked
    icon.source: entry?.icon ?? subMenu?.menuEntry?.icon ?? ""
    implicitWidth: 240
    implicitHeight: 32
    leftPadding: 10
    rightPadding: 10
    topPadding: 5
    bottomPadding: 5
    font.family: Theme.font
    font.pixelSize: 13
    hoverEnabled: true
    onTriggered: if (entry && !subMenu)
        entry.triggered()
    background: Rectangle {
        radius: 7
        color: root.down ? Theme.track : root.highlighted || root.hovered ? Theme.raised : "transparent"
    }
    indicator: null
    arrow: null
    contentItem: RowLayout {
        spacing: 8
        Item {
            Layout.preferredWidth: 16
            Layout.preferredHeight: 16
            visible: root.checkable || root.icon.source.toString() !== ""
            Image {
                anchors.fill: parent
                source: root.icon.source
                sourceSize: Qt.size(32, 32)
                fillMode: Image.PreserveAspectFit
                visible: !root.checkable
            }
            Text {
                anchors.centerIn: parent
                text: root.entry?.checkState === Qt.PartiallyChecked ? "−" : root.checked ? (root.entry?.buttonType === QsMenuButtonType.RadioButton ? "●" : "✓") : ""
                color: Theme.text
                font.pixelSize: 13
                visible: root.checkable
            }
        }
        Text {
            Layout.fillWidth: true
            text: root.text.replace(/&&/g, "\u0000").replace(/&(?=\w)/g, "").replace(/\u0000/g, "&")
            color: Theme.text
            font: root.font
            textFormat: Text.PlainText
            elide: Text.ElideRight
        }
        Icon {
            name: "chevron-right"
            visible: !!root.subMenu
            Layout.preferredWidth: 14
            Layout.preferredHeight: 14
        }
    }
    opacity: enabled ? 1 : 0.4
}
